import csv
from datetime import datetime, timedelta
from io import BytesIO, StringIO
from typing import Any

from django.conf import settings
from django.core.mail import EmailMessage, send_mail
from django.db import transaction
from django.db.models import Count, Q
from django.db.models.functions import TruncWeek
from django.template.loader import render_to_string
from django.utils import timezone

from apps.accounts.models import User
from apps.lessons.models import AttendanceStatus, Lesson, LessonStudent

from .models import AttendanceAlert, AttendanceReport

# WeasyPrint is optional - PDF generation will fail if not installed
# Note: WeasyPrint requires GTK/Pango system libraries which may not be available on Windows
try:
    from weasyprint import CSS, HTML
    from weasyprint.text.fonts import FontConfiguration

    WEASYPRINT_AVAILABLE = True
except (ImportError, OSError):
    # OSError is raised when GTK libraries are not available
    WEASYPRINT_AVAILABLE = False
    CSS = None
    HTML = None
    FontConfiguration = None


class AttendanceService:
    """Service for attendance operations."""

    def mark_attendance(
        self,
        lesson_id: str,
        student_id: str,
        status: str,
        notes: str | None = None,
        check_in_time: datetime | None = None,
        check_out_time: datetime | None = None,
    ) -> LessonStudent:
        """Mark attendance for a single student."""
        lesson_student = LessonStudent.objects.select_related(
            'lesson', 'student'
        ).get(
            lesson_id=lesson_id,
            student_id=student_id,
        )

        lesson_student.attendance_status = status
        lesson_student.attendance_notes = notes or ''
        lesson_student.attendance_marked_at = timezone.now()

        # Set check-in time for present/late
        if status in [AttendanceStatus.PRESENT, AttendanceStatus.LATE]:
            lesson_student.check_in_time = check_in_time or timezone.now()

        if check_out_time:
            lesson_student.check_out_time = check_out_time

        lesson_student.save()

        # Update lesson status
        self._update_lesson_status(lesson_id)

        return lesson_student

    @transaction.atomic
    def bulk_mark_attendance(
        self,
        lesson_id: str,
        attendance_records: list[dict[str, Any]],
    ) -> int:
        """Bulk mark attendance for multiple students."""
        updated_count = 0
        now = timezone.now()

        for record in attendance_records:
            student_id = record['student_id']
            status = record['status']

            check_in_time = None
            if status in [AttendanceStatus.PRESENT, AttendanceStatus.LATE]:
                check_in_time = record.get('check_in_time') or now

            LessonStudent.objects.filter(
                lesson_id=lesson_id,
                student_id=student_id,
            ).update(
                attendance_status=status,
                attendance_notes=record.get('notes', ''),
                attendance_marked_at=now,
                check_in_time=check_in_time,
                check_out_time=record.get('check_out_time'),
            )
            updated_count += 1

        # Update lesson status
        self._update_lesson_status(lesson_id)

        return updated_count

    def get_attendance_history(
        self,
        student_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> list[LessonStudent]:
        """Get attendance history for a student."""
        return list(
            LessonStudent.objects.filter(
                student_id=student_id,
                lesson__start_time__gte=start_date,
                lesson__start_time__lte=end_date,
            )
            .select_related(
                'lesson__subject',
                'lesson__level',
                'lesson__tutor',
                'lesson__room',
            )
            .order_by('-lesson__start_time')
        )

    def calculate_statistics(
        self,
        student_id: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Any]:
        """Calculate attendance statistics for a student.

        Only counts lessons that have already occurred (start_time <= now).
        """
        now = timezone.now()

        queryset = LessonStudent.objects.filter(
            student_id=student_id,
            lesson__start_time__lte=now,  # Only past lessons
            lesson__status__in=['completed', 'ongoing'],  # Only completed or ongoing
        )

        if start_date:
            # Make timezone aware if naive
            if start_date and timezone.is_naive(start_date):
                start_date = timezone.make_aware(start_date)
            queryset = queryset.filter(lesson__start_time__gte=start_date)
        if end_date:
            # Make timezone aware if naive
            if timezone.is_naive(end_date):
                end_date = timezone.make_aware(end_date)
            # Don't count future lessons even if end_date is in the future
            effective_end = min(end_date, now)
            queryset = queryset.filter(lesson__start_time__lte=effective_end)

        total = queryset.count()
        present = queryset.filter(attendance_status=AttendanceStatus.PRESENT).count()
        absent = queryset.filter(attendance_status=AttendanceStatus.ABSENT).count()
        late = queryset.filter(attendance_status=AttendanceStatus.LATE).count()
        excused = queryset.filter(attendance_status=AttendanceStatus.EXCUSED).count()
        pending = queryset.filter(attendance_status=AttendanceStatus.PENDING).count()

        attendance_rate = ((present + late) / total * 100) if total > 0 else 0

        return {
            'total': total,
            'present': present,
            'absent': absent,
            'late': late,
            'excused': excused,
            'pending': pending,
            'attendance_rate': round(attendance_rate, 2),
        }

    def get_students_with_low_attendance(
        self,
        threshold: int = 80,
    ) -> list[dict[str, Any]]:
        """Get students with attendance below threshold."""
        students = User.objects.filter(
            role='student',
            is_active=True,
        )

        students_at_risk = []

        for student in students:
            stats = self.calculate_statistics(str(student.id))
            if stats['total'] > 0 and stats['attendance_rate'] < threshold:
                students_at_risk.append({
                    'student': student,
                    'stats': stats,
                })

        return students_at_risk

    def check_in(self, lesson_id: str, student_id: str) -> LessonStudent:
        """Record check-in time."""
        lesson_student = LessonStudent.objects.select_related('lesson').get(
            lesson_id=lesson_id,
            student_id=student_id,
        )

        if not lesson_student.check_in_time:
            lesson_student.check_in_time = timezone.now()

            # Auto-set status if pending
            if lesson_student.attendance_status == AttendanceStatus.PENDING:
                lesson = lesson_student.lesson
                if timezone.now() > lesson.start_time + timedelta(minutes=10):
                    lesson_student.attendance_status = AttendanceStatus.LATE
                else:
                    lesson_student.attendance_status = AttendanceStatus.PRESENT

            lesson_student.attendance_marked_at = timezone.now()
            lesson_student.save()

        return lesson_student

    def check_out(self, lesson_id: str, student_id: str) -> LessonStudent:
        """Record check-out time."""
        lesson_student = LessonStudent.objects.get(
            lesson_id=lesson_id,
            student_id=student_id,
        )

        if lesson_student.check_in_time and not lesson_student.check_out_time:
            lesson_student.check_out_time = timezone.now()
            lesson_student.save()

        return lesson_student

    def _update_lesson_status(self, lesson_id: str) -> None:
        """Update lesson status based on attendance."""
        lesson = Lesson.objects.prefetch_related('lesson_students').get(pk=lesson_id)
        now = timezone.now()

        # Check if lesson has ended
        if lesson.end_time < now:
            all_marked = all(
                ls.attendance_status != AttendanceStatus.PENDING
                for ls in lesson.lesson_students.all()
            )

            if all_marked and lesson.status != 'completed':
                lesson.status = 'completed'
                lesson.save()

        elif lesson.start_time <= now < lesson.end_time:
            if lesson.status == 'scheduled':
                lesson.status = 'ongoing'
                lesson.save()

    def create_low_attendance_alert(
        self,
        student: User,
        attendance_rate: float,
        threshold: int = 80,
    ) -> AttendanceAlert:
        """Create an alert for low attendance."""
        return AttendanceAlert.objects.create(
            student=student,
            attendance_rate=attendance_rate,
            threshold=threshold,
            alert_type='LOW_ATTENDANCE',
        )

    def get_weekly_trend(
        self,
        student_id: str,
        weeks: int = 8,
    ) -> list[dict[str, Any]]:
        """Get weekly attendance trend data for a student.

        Only counts lessons that have already occurred.
        """
        now = timezone.now()
        start_date = now - timedelta(weeks=weeks)

        records = (
            LessonStudent.objects.filter(
                student_id=student_id,
                lesson__start_time__gte=start_date,
                lesson__start_time__lte=now,  # Only past lessons
                lesson__status__in=['completed', 'ongoing'],
            )
            .annotate(week=TruncWeek('lesson__start_time'))
            .values('week')
            .annotate(
                total=Count('id'),
                present=Count('id', filter=Q(attendance_status=AttendanceStatus.PRESENT)),
                late=Count('id', filter=Q(attendance_status=AttendanceStatus.LATE)),
                absent=Count('id', filter=Q(attendance_status=AttendanceStatus.ABSENT)),
            )
            .order_by('week')
        )

        return [
            {
                'week': r['week'],
                'total': r['total'],
                'present': r['present'],
                'late': r['late'],
                'absent': r['absent'],
                'rate': round(
                    ((r['present'] + r['late']) / r['total'] * 100)
                    if r['total'] > 0
                    else 0,
                    1,
                ),
            }
            for r in records
        ]

    def get_subject_breakdown(
        self,
        student_id: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """Get attendance breakdown by subject for a student.

        Only counts lessons that have already occurred.
        """
        now = timezone.now()

        queryset = LessonStudent.objects.filter(
            student_id=student_id,
            lesson__start_time__lte=now,  # Only past lessons
            lesson__status__in=['completed', 'ongoing'],
        ).select_related('lesson__subject')

        if start_date:
            if timezone.is_naive(start_date):
                start_date = timezone.make_aware(start_date)
            queryset = queryset.filter(lesson__start_time__gte=start_date)
        if end_date:
            if timezone.is_naive(end_date):
                end_date = timezone.make_aware(end_date)
            effective_end = min(end_date, now)
            queryset = queryset.filter(lesson__start_time__lte=effective_end)

        breakdown = (
            queryset.values('lesson__subject__name')
            .annotate(
                total=Count('id'),
                present=Count('id', filter=Q(attendance_status=AttendanceStatus.PRESENT)),
                late=Count('id', filter=Q(attendance_status=AttendanceStatus.LATE)),
                absent=Count('id', filter=Q(attendance_status=AttendanceStatus.ABSENT)),
                excused=Count('id', filter=Q(attendance_status=AttendanceStatus.EXCUSED)),
            )
            .order_by('lesson__subject__name')
        )

        return [
            {
                'subject': r['lesson__subject__name'],
                'total': r['total'],
                'present': r['present'],
                'late': r['late'],
                'absent': r['absent'],
                'excused': r['excused'],
                'rate': round(
                    ((r['present'] + r['late']) / r['total'] * 100)
                    if r['total'] > 0
                    else 0,
                    1,
                ),
            }
            for r in breakdown
        ]

    def get_tutor_statistics(
        self,
        tutor_id: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Any]:
        """Get attendance statistics for a tutor's lessons.

        Only counts lessons that have already occurred.
        """
        now = timezone.now()

        queryset = LessonStudent.objects.filter(
            lesson__tutor_id=tutor_id,
            lesson__start_time__lte=now,  # Only past lessons
            lesson__status__in=['completed', 'ongoing'],
        )

        if start_date:
            if timezone.is_naive(start_date):
                start_date = timezone.make_aware(start_date)
            queryset = queryset.filter(lesson__start_time__gte=start_date)
        if end_date:
            if timezone.is_naive(end_date):
                end_date = timezone.make_aware(end_date)
            effective_end = min(end_date, now)
            queryset = queryset.filter(lesson__start_time__lte=effective_end)

        total = queryset.count()
        present = queryset.filter(attendance_status=AttendanceStatus.PRESENT).count()
        absent = queryset.filter(attendance_status=AttendanceStatus.ABSENT).count()
        late = queryset.filter(attendance_status=AttendanceStatus.LATE).count()

        return {
            'total': total,
            'present': present,
            'absent': absent,
            'late': late,
            'attendance_rate': round(
                ((present + late) / total * 100) if total > 0 else 0,
                1,
            ),
        }


attendance_service = AttendanceService()


class AttendanceAlertService:
    """Service for managing attendance alerts."""

    DEFAULT_THRESHOLD = 80

    def check_and_create_alerts(
        self,
        threshold: int | None = None,
    ) -> list[AttendanceAlert]:
        """Check all students and create alerts for low attendance."""
        threshold = threshold or self.DEFAULT_THRESHOLD

        low_attendance = attendance_service.get_students_with_low_attendance(threshold)
        alerts = []

        for item in low_attendance:
            student = item['student']
            stats = item['stats']

            # Check if alert already exists for this period
            existing = AttendanceAlert.objects.filter(
                student=student,
                status=AttendanceAlert.AlertStatus.PENDING,
                threshold=threshold,
            ).exists()

            if existing:
                continue

            # Create alert
            alert = AttendanceAlert.objects.create(
                student=student,
                attendance_rate=stats['attendance_rate'],
                threshold=threshold,
                alert_type='LOW_ATTENDANCE',
                status=AttendanceAlert.AlertStatus.PENDING,
            )

            # Send notifications
            self._send_admin_alert(student, stats, threshold)

            if hasattr(student, 'student_profile') and student.student_profile.parent_email:
                self._send_parent_alert(student, stats, threshold)

            alerts.append(alert)

        return alerts

    def _send_admin_alert(
        self,
        student: User,
        stats: dict[str, Any],
        threshold: int,
    ) -> None:
        """Send alert email to admins."""
        admins = User.objects.filter(role='admin', is_active=True)

        for admin in admins:
            profile = getattr(student, 'student_profile', None)
            context = {
                'admin_name': admin.get_full_name(),
                'student_name': student.get_full_name(),
                'student_class': profile.class_name if profile else 'N/A',
                'attendance_rate': stats['attendance_rate'],
                'threshold': threshold,
                'total_lessons': stats['total'],
                'present_count': stats['present'],
                'absent_count': stats['absent'],
                'late_count': stats['late'],
            }

            html_content = render_to_string(
                'emails/low_attendance_admin.html',
                context,
            )

            send_mail(
                subject=f'Alert: Niska frekwencja - {student.get_full_name()}',
                message='',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[admin.email],
                html_message=html_content,
            )

    def _send_parent_alert(
        self,
        student: User,
        stats: dict[str, Any],
        threshold: int,
    ) -> None:
        """Send alert email to parent."""
        profile = student.student_profile

        if not profile.parent_email:
            return

        context = {
            'parent_name': profile.parent_name or 'Szanowni Rodzice',
            'student_name': student.get_full_name(),
            'attendance_rate': stats['attendance_rate'],
            'threshold': threshold,
            'total_lessons': stats['total'],
            'present_count': stats['present'],
            'absent_count': stats['absent'],
            'recommendation': 'Prosimy o kontakt z administratorem w celu omówienia sytuacji.',
        }

        html_content = render_to_string(
            'emails/low_attendance_parent.html',
            context,
        )

        send_mail(
            subject=f'Powiadomienie o frekwencji - {student.get_full_name()}',
            message='',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[profile.parent_email],
            html_message=html_content,
        )

    def get_active_alerts(self) -> list[AttendanceAlert]:
        """Get all pending alerts."""
        return list(
            AttendanceAlert.objects.filter(
                status=AttendanceAlert.AlertStatus.PENDING,
            )
            .select_related('student', 'student__student_profile')
            .order_by('-created_at')
        )

    def resolve_alert(
        self,
        alert_id: int,
        resolution: str,
    ) -> AttendanceAlert:
        """Mark alert as resolved."""
        alert = AttendanceAlert.objects.get(id=alert_id)
        alert.status = AttendanceAlert.AlertStatus.RESOLVED
        alert.resolution = resolution
        alert.resolved_at = timezone.now()
        alert.save()
        return alert

    def dismiss_alert(self, alert_id: int) -> AttendanceAlert:
        """Dismiss an alert."""
        alert = AttendanceAlert.objects.get(id=alert_id)
        alert.status = AttendanceAlert.AlertStatus.DISMISSED
        alert.resolved_at = timezone.now()
        alert.save()
        return alert


alert_service = AttendanceAlertService()


class AttendanceReportService:
    """Service for generating attendance reports."""

    def generate_monthly_report(
        self,
        student: User,
        month: datetime,
    ) -> tuple[AttendanceReport, BytesIO]:
        """Generate monthly attendance report PDF for a student."""
        if not WEASYPRINT_AVAILABLE:
            raise ImportError(
                'WeasyPrint is required for PDF generation. '
                'Install it with: pip install weasyprint'
            )

        # Calculate month boundaries
        if isinstance(month, str):
            month = datetime.strptime(month, '%Y-%m')

        year = month.year
        month_num = month.month

        # First and last day of month
        start_date = timezone.make_aware(datetime(year, month_num, 1))
        if month_num == 12:
            end_date = timezone.make_aware(datetime(year + 1, 1, 1))
        else:
            end_date = timezone.make_aware(datetime(year, month_num + 1, 1))

        # Get attendance records
        records = (
            LessonStudent.objects.filter(
                student=student,
                lesson__start_time__gte=start_date,
                lesson__start_time__lt=end_date,
            )
            .select_related('lesson', 'lesson__subject', 'lesson__tutor')
            .order_by('lesson__start_time')
        )

        # Calculate statistics
        stats = attendance_service.calculate_statistics(
            str(student.id),
            start_date,
            end_date,
        )

        # Prepare context
        context = {
            'student': student,
            'month': month,
            'month_name': month.strftime('%B %Y'),
            'statistics': stats,
            'records': records,
            'generated_at': timezone.now(),
        }

        # Render HTML
        html_content = render_to_string('reports/attendance_monthly.html', context)

        # Generate PDF
        font_config = FontConfiguration()
        css = CSS(
            string='''
            @page {
                size: A4;
                margin: 2cm;
            }
            body {
                font-family: 'Roboto', sans-serif;
                font-size: 10pt;
                line-height: 1.4;
            }
            .header {
                border-bottom: 2px solid #3B82F6;
                padding-bottom: 10px;
                margin-bottom: 20px;
            }
            .title {
                font-size: 24pt;
                font-weight: bold;
                color: #1F2937;
            }
            .subtitle {
                font-size: 10pt;
                color: #6B7280;
            }
            .stats-grid {
                display: flex;
                justify-content: space-between;
                margin-bottom: 20px;
            }
            .stat-box {
                flex: 1;
                padding: 10px;
                margin: 0 5px;
                background-color: #F9FAFB;
                border-radius: 5px;
                text-align: center;
            }
            .stat-value {
                font-size: 20pt;
                font-weight: bold;
            }
            .stat-label {
                font-size: 8pt;
                color: #6B7280;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }
            th {
                background-color: #3B82F6;
                color: white;
                padding: 8px;
                text-align: left;
                font-size: 9pt;
            }
            td {
                padding: 8px;
                border-bottom: 1px solid #E5E7EB;
                font-size: 8pt;
            }
            .status-present { color: #10B981; }
            .status-late { color: #F59E0B; }
            .status-absent { color: #EF4444; }
            .status-excused { color: #3B82F6; }
            .footer {
                position: fixed;
                bottom: 0;
                left: 0;
                right: 0;
                text-align: center;
                font-size: 8pt;
                color: #9CA3AF;
                border-top: 1px solid #E5E7EB;
                padding-top: 10px;
            }
        ''',
            font_config=font_config,
        )

        html = HTML(string=html_content)
        pdf_buffer = BytesIO()
        html.write_pdf(pdf_buffer, stylesheets=[css], font_config=font_config)
        pdf_buffer.seek(0)

        # Save report record
        report, _ = AttendanceReport.objects.update_or_create(
            student=student,
            month=start_date,
            defaults={
                'attendance_rate': stats['attendance_rate'],
                'total_lessons': stats['total'],
                'present_count': stats['present'],
                'absent_count': stats['absent'],
                'late_count': stats['late'],
                'excused_count': stats['excused'],
            },
        )

        return report, pdf_buffer

    def generate_and_send_monthly_reports(
        self,
        month: datetime,
    ) -> list[dict[str, Any]]:
        """Generate and email monthly reports for all students."""
        students = User.objects.filter(
            role='student',
            is_active=True,
        ).select_related('student_profile')

        results = []

        for student in students:
            try:
                report, pdf_buffer = self.generate_monthly_report(student, month)

                # Send to parent if email available
                profile = getattr(student, 'student_profile', None)
                if profile and profile.parent_email:
                    self._send_report_email(student, report, pdf_buffer, month)

                results.append(
                    {
                        'student': student,
                        'report': report,
                        'success': True,
                    }
                )
            except Exception as e:
                results.append(
                    {
                        'student': student,
                        'success': False,
                        'error': str(e),
                    }
                )

        return results

    def _send_report_email(
        self,
        student: User,
        report: AttendanceReport,
        pdf_buffer: BytesIO,
        month: datetime,
    ) -> None:
        """Send monthly report email to parent."""
        profile = student.student_profile

        context = {
            'parent_name': profile.parent_name or 'Szanowni Rodzice',
            'student_name': student.get_full_name(),
            'month': month.strftime('%B %Y'),
            'attendance_rate': report.attendance_rate,
        }

        html_content = render_to_string(
            'emails/monthly_attendance_report.html',
            context,
        )

        email = EmailMessage(
            subject=f"Raport frekwencji - {month.strftime('%B %Y')}",
            body=html_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[profile.parent_email],
        )
        email.content_subtype = 'html'

        # Attach PDF
        pdf_buffer.seek(0)
        email.attach(
            f"raport-frekwencji-{month.strftime('%Y-%m')}.pdf",
            pdf_buffer.getvalue(),
            'application/pdf',
        )

        email.send()


report_service = AttendanceReportService()


class AttendanceExportService:
    """Service for exporting attendance data."""

    STATUS_LABELS = {
        'PRESENT': 'Obecny',
        'LATE': 'Spóźniony',
        'ABSENT': 'Nieobecny',
        'EXCUSED': 'Usprawiedliwiony',
        'PENDING': 'Oczekujące',
    }

    def export_to_csv(
        self,
        start_date: datetime,
        end_date: datetime,
        student_id: str | None = None,
        subject_id: int | None = None,
    ) -> str:
        """Export attendance records to CSV."""
        queryset = (
            LessonStudent.objects.filter(
                lesson__start_time__gte=start_date,
                lesson__start_time__lte=end_date,
            )
            .select_related(
                'student',
                'student__student_profile',
                'lesson',
                'lesson__subject',
                'lesson__tutor',
            )
            .order_by('-lesson__start_time')
        )

        if student_id:
            queryset = queryset.filter(student_id=student_id)

        if subject_id:
            queryset = queryset.filter(lesson__subject_id=subject_id)

        # Create CSV
        output = StringIO()
        # Add BOM for Excel compatibility
        output.write('\ufeff')

        writer = csv.writer(output)

        # Header
        writer.writerow(
            [
                'Data',
                'Godzina',
                'Uczeń',
                'Klasa',
                'Przedmiot',
                'Korepetytor',
                'Status',
                'Notatki',
            ]
        )

        # Data rows
        for record in queryset:
            profile = getattr(record.student, 'student_profile', None)
            writer.writerow(
                [
                    record.lesson.start_time.strftime('%d.%m.%Y'),
                    record.lesson.start_time.strftime('%H:%M'),
                    record.student.get_full_name(),
                    profile.class_name if profile else 'N/A',
                    record.lesson.subject.name,
                    record.lesson.tutor.get_full_name(),
                    self.STATUS_LABELS.get(record.attendance_status, record.attendance_status),
                    record.attendance_notes or '',
                ]
            )

        return output.getvalue()


export_service = AttendanceExportService()
