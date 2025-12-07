import json
from datetime import datetime, timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import FileResponse, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

from apps.accounts.models import User
from apps.core.mixins import AdminRequiredMixin, HTMXMixin, TutorRequiredMixin
from apps.lessons.models import AttendanceStatus, Lesson
from apps.subjects.models import Subject

from .models import AttendanceAlert
from .services import alert_service, attendance_service, export_service, report_service

# Polish month names
POLISH_MONTHS = [
    '', 'Styczen', 'Luty', 'Marzec', 'Kwiecien', 'Maj', 'Czerwiec',
    'Lipiec', 'Sierpien', 'Wrzesien', 'Pazdziernik', 'Listopad', 'Grudzien'
]


class AttendanceOverviewView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, TemplateView):
    """Overview of all students attendance."""

    template_name = 'attendance/overview.html'
    partial_template_name = 'attendance/partials/_overview_table.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get selected month or default to current
        selected_month = self.request.GET.get('month')
        today = datetime.now()

        if selected_month:
            year, month = map(int, selected_month.split('-'))
        else:
            year, month = today.year, today.month
            selected_month = f'{year}-{month:02d}'

        # Calculate date range for selected month
        start_date = timezone.make_aware(datetime(year, month, 1))
        if month == 12:
            end_date = timezone.make_aware(datetime(year + 1, 1, 1))
        else:
            end_date = timezone.make_aware(datetime(year, month + 1, 1))

        # Get all students with their stats
        students = User.objects.filter(
            role='student',
            is_active=True,
        ).select_related('student_profile').order_by('last_name', 'first_name')

        students_data = []
        total_rate = 0
        above_threshold = 0
        below_threshold = 0

        for student in students:
            stats = attendance_service.calculate_statistics(
                str(student.id),
                start_date,
                end_date,
            )
            students_data.append({
                'student': student,
                'stats': stats,
            })

            if stats['total'] > 0:
                total_rate += stats['attendance_rate']
                if stats['attendance_rate'] >= 80:
                    above_threshold += 1
                else:
                    below_threshold += 1

        # Calculate average
        students_with_lessons = above_threshold + below_threshold
        avg_rate = round(total_rate / students_with_lessons, 1) if students_with_lessons > 0 else 0

        context['students'] = students_data
        context['selected_month'] = selected_month
        context['summary'] = {
            'total_students': len(students),
            'avg_rate': avg_rate,
            'above_threshold': above_threshold,
            'below_threshold': below_threshold,
        }

        # Generate month options (last 12 months)
        months = []
        for i in range(12):
            m_date = today - timedelta(days=30 * i)
            m_value = f'{m_date.year}-{m_date.month:02d}'
            m_label = f'{POLISH_MONTHS[m_date.month]} {m_date.year}'
            months.append({'value': m_value, 'label': m_label})

        context['months'] = months

        return context


class AttendanceMarkingView(LoginRequiredMixin, TutorRequiredMixin, HTMXMixin, TemplateView):
    """View for marking attendance."""

    template_name = 'attendance/marking.html'
    partial_template_name = 'attendance/partials/_attendance_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lesson_id = self.kwargs.get('lesson_id')

        lesson = get_object_or_404(
            Lesson.objects.select_related(
                'subject', 'level', 'tutor', 'room'
            ).prefetch_related(
                'lesson_students__student'
            ),
            pk=lesson_id,
        )

        context['lesson'] = lesson
        context['students'] = lesson.lesson_students.select_related('student').all()
        context['statuses'] = AttendanceStatus.choices

        return context


class MarkAttendanceAPIView(LoginRequiredMixin, TutorRequiredMixin, View):
    """API endpoint for marking attendance."""

    def post(self, request, lesson_id):
        try:
            data = json.loads(request.body)
            student_id = data.get('student_id')
            status = data.get('status')
            notes = data.get('notes', '')

            lesson_student = attendance_service.mark_attendance(
                lesson_id=str(lesson_id),
                student_id=student_id,
                status=status,
                notes=notes,
            )

            return JsonResponse({
                'success': True,
                'status': lesson_student.attendance_status,
                'marked_at': lesson_student.attendance_marked_at.isoformat(),
            })

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


class BulkMarkAttendanceView(LoginRequiredMixin, TutorRequiredMixin, View):
    """View for bulk marking attendance via HTMX."""

    def post(self, request, lesson_id):
        records = []

        for key, value in request.POST.items():
            if key.startswith('status_'):
                student_id = key.replace('status_', '')
                notes_key = f'notes_{student_id}'

                if value and value != 'PENDING':
                    records.append({
                        'student_id': student_id,
                        'status': value,
                        'notes': request.POST.get(notes_key, ''),
                    })

        if records:
            attendance_service.bulk_mark_attendance(
                lesson_id=str(lesson_id),
                attendance_records=records,
            )

            return HttpResponse(
                status=204,
                headers={
                    'HX-Trigger': 'attendanceSaved',
                    'HX-Reswap': 'none',
                },
            )

        return HttpResponse('Brak zmian do zapisania', status=400)


class CheckInView(LoginRequiredMixin, View):
    """Check-in endpoint."""

    def post(self, request, lesson_id, student_id):
        try:
            lesson_student = attendance_service.check_in(
                lesson_id=str(lesson_id),
                student_id=str(student_id),
            )

            if getattr(request, 'htmx', False):
                return HttpResponse(
                    f'<span class="badge badge-success">'
                    f'{lesson_student.check_in_time.strftime("%H:%M:%S")}</span>'
                )

            return JsonResponse({
                'success': True,
                'check_in_time': lesson_student.check_in_time.isoformat(),
            })

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


class CheckOutView(LoginRequiredMixin, View):
    """Check-out endpoint."""

    def post(self, request, lesson_id, student_id):
        try:
            lesson_student = attendance_service.check_out(
                lesson_id=str(lesson_id),
                student_id=str(student_id),
            )

            if getattr(request, 'htmx', False):
                return HttpResponse(
                    f'<span class="badge badge-success">'
                    f'{lesson_student.check_out_time.strftime("%H:%M:%S")}</span>'
                )

            return JsonResponse({
                'success': True,
                'check_out_time': lesson_student.check_out_time.isoformat(),
            })

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


class AttendanceHistoryView(LoginRequiredMixin, HTMXMixin, TemplateView):
    """View attendance history for a student."""

    template_name = 'attendance/history.html'
    partial_template_name = 'attendance/partials/_history_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student_id = self.kwargs.get('student_id')

        # Get date range from query params
        start_date_str = self.request.GET.get('start_date')
        end_date_str = self.request.GET.get('end_date')

        if not start_date_str:
            start_date = timezone.now() - timedelta(days=30)
        else:
            start_date = timezone.datetime.fromisoformat(start_date_str)

        if not end_date_str:
            end_date = timezone.now()
        else:
            end_date = timezone.datetime.fromisoformat(end_date_str)

        context['history'] = attendance_service.get_attendance_history(
            student_id=str(student_id),
            start_date=start_date,
            end_date=end_date,
        )
        context['statistics'] = attendance_service.calculate_statistics(
            student_id=str(student_id),
            start_date=start_date,
            end_date=end_date,
        )
        context['start_date'] = start_date
        context['end_date'] = end_date

        return context


# Statistics Views
class StudentStatisticsView(LoginRequiredMixin, HTMXMixin, TemplateView):
    """Display attendance statistics for a student."""

    template_name = 'attendance/statistics/student_stats.html'
    partial_template_name = 'attendance/statistics/partials/_stats_content.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student_id = self.kwargs.get('student_id') or self.request.user.id

        # Date range from query params
        start_date_str = self.request.GET.get('start_date')
        end_date_str = self.request.GET.get('end_date')

        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        else:
            start_date = datetime.now() - timedelta(days=90)

        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        else:
            end_date = datetime.now()

        student = get_object_or_404(User, id=student_id)

        context['student'] = student
        context['stats'] = attendance_service.calculate_statistics(
            str(student.id),
            start_date,
            end_date,
        )
        context['weekly_trend'] = attendance_service.get_weekly_trend(str(student.id))
        context['subject_breakdown'] = attendance_service.get_subject_breakdown(
            str(student.id),
            start_date,
            end_date,
        )
        context['start_date'] = start_date
        context['end_date'] = end_date

        return context


class AttendanceChartDataView(LoginRequiredMixin, View):
    """API endpoint for chart data (JSON)."""

    def get(self, request, student_id):
        student = get_object_or_404(User, id=student_id)

        weeks = int(request.GET.get('weeks', 8))
        trend_data = attendance_service.get_weekly_trend(str(student.id), weeks)

        return JsonResponse(
            {
                'labels': [d['week'].strftime('%d %b') for d in trend_data],
                'rates': [d['rate'] for d in trend_data],
                'present': [d['present'] for d in trend_data],
                'absent': [d['absent'] for d in trend_data],
            }
        )


class LowAttendanceListView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, TemplateView):
    """Display students with low attendance."""

    template_name = 'attendance/statistics/low_attendance.html'
    partial_template_name = 'attendance/statistics/partials/_low_attendance_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        threshold = int(self.request.GET.get('threshold', 80))
        days = int(self.request.GET.get('days', 30))

        context['students'] = attendance_service.get_students_with_low_attendance(threshold)
        context['threshold'] = threshold
        context['days'] = days

        return context


# Alert Views
class AttendanceAlertListView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, TemplateView):
    """Display active attendance alerts."""

    template_name = 'attendance/alerts/list.html'
    partial_template_name = 'attendance/alerts/partials/_alert_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['alerts'] = alert_service.get_active_alerts()
        return context


class CheckAlertsView(LoginRequiredMixin, AdminRequiredMixin, View):
    """Manually trigger alert check."""

    def post(self, request):
        threshold = int(request.POST.get('threshold', 80))
        alerts = alert_service.check_and_create_alerts(threshold)

        return HttpResponse(
            f'<div class="alert alert-success">Utworzono {len(alerts)} nowych alertów.</div>'
        )


class ResolveAlertFormView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    """Display resolve alert form."""

    template_name = 'attendance/alerts/partials/_resolve_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        alert_id = self.kwargs.get('alert_id')
        context['alert'] = get_object_or_404(AttendanceAlert, id=alert_id)
        return context


class ResolveAlertView(LoginRequiredMixin, AdminRequiredMixin, View):
    """Resolve an attendance alert."""

    def post(self, request, alert_id):
        resolution = request.POST.get('resolution', '')

        if not resolution.strip():
            return HttpResponse(
                '<div class="alert alert-error">Opis rozwiązania jest wymagany.</div>',
                status=400,
            )

        alert_service.resolve_alert(alert_id, resolution)

        return HttpResponse(
            status=204,
            headers={'HX-Trigger': 'alertResolved'},
        )


class DismissAlertView(LoginRequiredMixin, AdminRequiredMixin, View):
    """Dismiss an attendance alert."""

    def post(self, request, alert_id):
        alert_service.dismiss_alert(alert_id)

        return HttpResponse(
            status=204,
            headers={'HX-Trigger': 'alertDismissed'},
        )


# Report Views
class GenerateReportView(LoginRequiredMixin, View):
    """Generate and download attendance report PDF."""

    def get(self, request, student_id):
        student = get_object_or_404(User, id=student_id)

        # Get month from query params or use previous month
        month_str = request.GET.get('month')
        if month_str:
            month = datetime.strptime(month_str, '%Y-%m')
        else:
            today = datetime.now()
            if today.month == 1:
                month = datetime(today.year - 1, 12, 1)
            else:
                month = datetime(today.year, today.month - 1, 1)

        report, pdf_buffer = report_service.generate_monthly_report(student, month)

        filename = (
            f"raport-frekwencji-{student.get_full_name().replace(' ', '-')}-"
            f"{month.strftime('%Y-%m')}.pdf"
        )

        return FileResponse(
            pdf_buffer,
            as_attachment=True,
            filename=filename,
            content_type='application/pdf',
        )


class BulkGenerateReportsView(LoginRequiredMixin, AdminRequiredMixin, View):
    """Generate monthly reports for all students."""

    def post(self, request):
        month_str = request.POST.get('month')
        if month_str:
            month = datetime.strptime(month_str, '%Y-%m')
        else:
            today = datetime.now()
            if today.month == 1:
                month = datetime(today.year - 1, 12, 1)
            else:
                month = datetime(today.year, today.month - 1, 1)

        # Queue task for background processing
        from .tasks import generate_monthly_reports_task

        generate_monthly_reports_task.delay(month.isoformat())

        return HttpResponse(
            '<div class="alert alert-success">Generowanie raportów zostało zaplanowane. '
            'Raporty zostaną wysłane emailem.</div>'
        )


# Export Views
class ExportCSVView(LoginRequiredMixin, AdminRequiredMixin, View):
    """Export attendance data to CSV."""

    def get(self, request):
        # Parse dates from query params
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        student_id = request.GET.get('student_id')
        subject_id = request.GET.get('subject_id')

        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        else:
            start_date = datetime.now() - timedelta(days=30)

        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        else:
            end_date = datetime.now()

        csv_content = export_service.export_to_csv(
            start_date,
            end_date,
            student_id,
            int(subject_id) if subject_id else None,
        )

        filename = (
            f"frekwencja-{start_date.strftime('%Y-%m-%d')}-{end_date.strftime('%Y-%m-%d')}.csv"
        )

        response = HttpResponse(csv_content, content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        return response


class ExportModalView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    """Display export modal with filters."""

    template_name = 'attendance/partials/_export_modal.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['students'] = User.objects.filter(role='student', is_active=True).order_by(
            'last_name', 'first_name'
        )
        context['subjects'] = Subject.objects.all().order_by('name')
        return context


class ExportPageView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    """Display export page with filters and bulk report generation."""

    template_name = 'attendance/export.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['students'] = User.objects.filter(role='student', is_active=True).order_by(
            'last_name', 'first_name'
        )
        context['subjects'] = Subject.objects.all().order_by('name')

        # Calculate previous month for default value
        today = datetime.now()
        if today.month == 1:
            prev_month = datetime(today.year - 1, 12, 1)
        else:
            prev_month = datetime(today.year, today.month - 1, 1)
        context['previous_month'] = prev_month.strftime('%Y-%m')

        return context
