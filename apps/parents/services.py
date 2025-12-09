"""Services for parent portal operations."""

from datetime import timedelta
from typing import Any

from django.db.models import Count, Q
from django.utils import timezone

from apps.accounts.models import ParentAccess, User
from apps.lessons.models import LessonStudent
from apps.students.models import StudentProfile


class ParentDashboardService:
    """Service for parent portal operations."""

    @classmethod
    def get_children(cls, parent_user) -> list[dict[str, Any]]:
        """Get list of children for parent."""
        children = []

        # Admin can see all students
        if parent_user.is_admin:
            students = User.objects.filter(
                role='student', is_active=True
            ).select_related('student_profile')[:10]  # Limit for admin

            for student in students:
                try:
                    profile = student.student_profile
                    class_name = profile.class_name
                except StudentProfile.DoesNotExist:
                    class_name = ''

                children.append({
                    'id': student.id,
                    'name': student.first_name,
                    'surname': student.last_name,
                    'class_name': class_name,
                })
            return children

        # For parents with role='parent', use ParentAccess
        if parent_user.is_parent:
            parent_access_list = ParentAccess.objects.filter(
                parent=parent_user,
                is_active=True,
            ).select_related('student', 'student__student_profile')

            for access in parent_access_list:
                student = access.student
                try:
                    profile = student.student_profile
                    class_name = profile.class_name
                except StudentProfile.DoesNotExist:
                    class_name = ''

                children.append({
                    'id': student.id,
                    'name': student.first_name,
                    'surname': student.last_name,
                    'class_name': class_name,
                })

        return children

    @classmethod
    def get_student_info(cls, student) -> dict[str, Any] | None:
        """Get basic student info for parent dashboard."""
        try:
            profile = student.student_profile
            return {
                'id': student.id,
                'name': student.first_name,
                'surname': student.last_name,
                'email': student.email,
                'class_name': profile.class_name,
                'parent_name': profile.parent_name,
                'parent_email': profile.parent_email,
                'parent_phone': profile.parent_phone,
            }
        except StudentProfile.DoesNotExist:
            return {
                'id': student.id,
                'name': student.first_name,
                'surname': student.last_name,
                'email': student.email,
                'class_name': '',
                'parent_name': '',
                'parent_email': '',
                'parent_phone': '',
            }

    @classmethod
    def get_student_stats(cls, student) -> dict[str, Any]:
        """Get comprehensive stats for student."""
        today = timezone.now().date()
        month_start = today.replace(day=1)
        thirty_days_ago = timezone.now() - timedelta(days=30)

        # Attendance stats (using LessonStudent)
        lessons = LessonStudent.objects.filter(
            student=student, lesson__status='completed'
        )
        total_lessons = lessons.count()
        present_count = lessons.filter(attendance_status='PRESENT').count()

        attendance_rate = 0
        if total_lessons > 0:
            attendance_rate = round((present_count / total_lessons) * 100)

        # Monthly lessons
        monthly_lessons = LessonStudent.objects.filter(
            student=student,
            lesson__start_time__gte=month_start,
            lesson__status__in=['scheduled', 'completed'],
        ).count()

        # Monthly hours calculation
        monthly_completed = LessonStudent.objects.filter(
            student=student,
            lesson__start_time__gte=month_start,
            lesson__status='completed',
        ).select_related('lesson')

        monthly_minutes = 0
        for ls in monthly_completed:
            duration = (ls.lesson.end_time - ls.lesson.start_time).seconds // 60
            monthly_minutes += duration

        # Achievements count
        achievements_count = cls._calculate_achievements(student)

        return {
            'attendance_rate': attendance_rate,
            'present_count': present_count,
            'total_lessons': total_lessons,
            'monthly_lessons': monthly_lessons,
            'monthly_hours': round(monthly_minutes / 60, 1),
            'average_grade': 75,  # placeholder
            'grade_count': 0,
            'achievements_count': achievements_count,
        }

    @classmethod
    def get_upcoming_lessons(cls, student, limit: int = 5):
        """Get upcoming lessons for student."""
        return (
            LessonStudent.objects.filter(
                student=student,
                lesson__start_time__gt=timezone.now(),
                lesson__status='scheduled',
            )
            .select_related('lesson', 'lesson__tutor', 'lesson__subject')
            .order_by('lesson__start_time')[:limit]
        )

    @classmethod
    def get_recent_attendance(cls, student, start_date, end_date):
        """Get attendance records for date range."""
        return (
            LessonStudent.objects.filter(
                student=student,
                lesson__start_time__gte=start_date,
                lesson__start_time__lte=end_date,
                lesson__status='completed',
            )
            .select_related('lesson', 'lesson__tutor')
            .order_by('-lesson__start_time')
        )

    @classmethod
    def get_pending_invoices(cls, student):
        """Get pending invoices for student."""
        from apps.invoices.models import Invoice, InvoiceStatus

        return Invoice.objects.filter(
            student=student,
            status__in=[InvoiceStatus.GENERATED, InvoiceStatus.SENT, InvoiceStatus.OVERDUE],
        ).order_by('-issue_date')[:5]

    @classmethod
    def _calculate_achievements(cls, student) -> int:
        """Calculate unlocked achievements for student."""
        achievements = 0

        if LessonStudent.objects.filter(
            student=student, attendance_status='PRESENT'
        ).exists():
            achievements += 1

        if (
            LessonStudent.objects.filter(
                student=student, attendance_status='PRESENT'
            ).count()
            >= 10
        ):
            achievements += 1

        return achievements


class ParentAttendanceService:
    """Service for parent attendance monitoring."""

    @classmethod
    def get_attendance_history(cls, student, start_date, end_date):
        """Get attendance history for date range."""
        return (
            LessonStudent.objects.filter(
                student=student,
                lesson__start_time__gte=start_date,
                lesson__start_time__lte=end_date,
            )
            .select_related('lesson', 'lesson__subject', 'lesson__tutor')
            .order_by('-lesson__start_time')
        )

    @classmethod
    def get_attendance_stats(cls, student, month: str) -> dict[str, Any]:
        """Get attendance statistics for a month."""
        year, month_num = map(int, month.split('-'))

        attendance = LessonStudent.objects.filter(
            student=student,
            lesson__start_time__year=year,
            lesson__start_time__month=month_num,
            lesson__status='completed',
        )

        total = attendance.count()
        present_count = attendance.filter(attendance_status='PRESENT').count()
        absent_count = attendance.filter(attendance_status='ABSENT').count()
        late_count = attendance.filter(attendance_status='LATE').count()
        excused_count = attendance.filter(attendance_status='EXCUSED').count()

        attendance_rate = 0
        if total > 0:
            attendance_rate = round((present_count / total) * 100)

        return {
            'present_count': present_count,
            'absent_count': absent_count,
            'late_count': late_count,
            'excused_count': excused_count,
            'total': total,
            'attendance_rate': attendance_rate,
        }


class ParentInvoiceService:
    """Service for parent invoice operations."""

    @classmethod
    def get_invoices(cls, student):
        """Get all invoices for student."""
        from apps.invoices.models import Invoice

        return Invoice.objects.filter(
            student=student
        ).order_by('-issue_date')

    @classmethod
    def get_invoice_summary(cls, student) -> dict[str, Any]:
        """Get invoice summary for student."""
        from decimal import Decimal

        from django.db.models import Sum

        from apps.invoices.models import Invoice, InvoiceStatus

        year_start = timezone.now().replace(month=1, day=1)

        # Year totals
        year_invoices = Invoice.objects.filter(
            student=student,
            issue_date__gte=year_start,
        )
        year_total = year_invoices.aggregate(
            total=Sum('total_amount')
        )['total'] or Decimal('0')

        # Pending invoices
        pending_invoices = Invoice.objects.filter(
            student=student,
            status__in=[InvoiceStatus.GENERATED, InvoiceStatus.SENT],
        )
        pending_total = pending_invoices.aggregate(
            total=Sum('total_amount')
        )['total'] or Decimal('0')

        # Overdue invoices
        overdue_invoices = Invoice.objects.filter(
            student=student,
            status=InvoiceStatus.OVERDUE,
        )
        overdue_total = overdue_invoices.aggregate(
            total=Sum('total_amount')
        )['total'] or Decimal('0')

        return {
            'year_total': year_total,
            'year_invoices_count': year_invoices.count(),
            'pending_total': pending_total,
            'pending_count': pending_invoices.count(),
            'overdue_total': overdue_total,
            'overdue_count': overdue_invoices.count(),
        }


class ParentTutorService:
    """Service for parent-tutor communication."""

    @classmethod
    def get_student_tutors(cls, student) -> list[dict[str, Any]]:
        """Get tutors teaching this student."""
        tutor_ids = (
            LessonStudent.objects.filter(student=student)
            .values_list('lesson__tutor_id', flat=True)
            .distinct()
        )

        tutors = User.objects.filter(id__in=tutor_ids, role='tutor')

        result = []
        for tutor in tutors:
            # Get lesson counts
            lessons = LessonStudent.objects.filter(
                student=student, lesson__tutor=tutor
            )

            completed = lessons.filter(lesson__status='completed').count()
            upcoming = lessons.filter(
                lesson__status='scheduled', lesson__start_time__gt=timezone.now()
            ).count()

            # Get subjects taught to this student
            subjects = lessons.values_list(
                'lesson__subject__name', flat=True
            ).distinct()

            # Get tutor profile info
            try:
                profile = tutor.tutor_profile
                bio = profile.bio
                experience_years = profile.experience_years
                rating = getattr(profile, 'rating', None)
            except Exception:
                bio = ''
                experience_years = 0
                rating = None

            result.append(
                {
                    'id': tutor.id,
                    'name': tutor.first_name,
                    'surname': tutor.last_name,
                    'email': tutor.email,
                    'bio': bio,
                    'experience_years': experience_years,
                    'rating': rating,
                    'subjects': list(filter(None, subjects)),
                    'completed_lessons': completed,
                    'upcoming_lessons': upcoming,
                }
            )

        return result
