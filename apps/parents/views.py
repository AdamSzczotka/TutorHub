"""Views for parent portal."""

from datetime import timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.generic import TemplateView, View

from apps.accounts.models import User
from apps.core.mixins import HTMXMixin, ParentAccessMixin, ParentRequiredMixin
from apps.parents.services import (
    ParentAttendanceService,
    ParentDashboardService,
    ParentInvoiceService,
    ParentTutorService,
)


class ParentDashboardView(LoginRequiredMixin, ParentRequiredMixin, HTMXMixin, TemplateView):
    """Parent portal dashboard view."""

    template_name = 'parent_panel/dashboard.html'
    partial_template_name = 'parent_panel/partials/_dashboard_content.html'

    def _has_access_to_student(self, student_id: int) -> bool:
        """Verify current user has parent access to student."""
        children = ParentDashboardService.get_children(self.request.user)
        child_ids = [c['id'] for c in children]
        return student_id in child_ids or self.request.user.is_admin

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get children
        children = ParentDashboardService.get_children(self.request.user)
        context['children'] = children

        # Get selected child (default to first)
        student_id = self.request.GET.get('student_id')
        selected_student = None

        if student_id:
            # Validate access to requested student
            try:
                student_id_int = int(student_id)
            except ValueError:
                from django.http import Http404

                raise Http404('Nieprawidłowy identyfikator ucznia') from None

            if not self._has_access_to_student(student_id_int):
                from django.core.exceptions import PermissionDenied

                raise PermissionDenied('Brak dostępu do danych tego ucznia')
            selected_student = get_object_or_404(User, pk=student_id_int, role='student')
        elif children:
            selected_student = get_object_or_404(User, pk=children[0]['id'])

        if selected_student:
            context['selected_student'] = ParentDashboardService.get_student_info(
                selected_student
            )
            context['stats'] = ParentDashboardService.get_student_stats(selected_student)
            context['upcoming_lessons'] = ParentDashboardService.get_upcoming_lessons(
                selected_student
            )

            # Recent attendance (last 7 days)
            today = timezone.now().date()
            week_ago = today - timedelta(days=7)
            context['recent_attendance'] = ParentDashboardService.get_recent_attendance(
                selected_student, week_ago, today
            )

            # Pending invoices
            context['pending_invoices'] = ParentDashboardService.get_pending_invoices(
                selected_student
            )

        return context


class ParentChildSelectView(LoginRequiredMixin, ParentRequiredMixin, View):
    """Handle child selection for parent portal."""

    def get(self, request, student_id):
        children = ParentDashboardService.get_children(request.user)
        child_ids = [c['id'] for c in children]

        if student_id not in child_ids and not request.user.is_admin:
            return JsonResponse({'error': 'Brak dostępu'}, status=403)

        # Redirect to dashboard with selected student
        return JsonResponse({'redirect': f'/parent/?student_id={student_id}'})


class ParentAttendanceView(LoginRequiredMixin, ParentAccessMixin, HTMXMixin, TemplateView):
    """View attendance history for a student."""

    template_name = 'parent_panel/attendance/list.html'
    partial_template_name = 'parent_panel/attendance/partials/_attendance_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.request.current_student

        # Get month parameter (default to current month)
        month = self.request.GET.get('month')
        if not month:
            month = timezone.now().strftime('%Y-%m')

        year, month_num = map(int, month.split('-'))
        from datetime import date

        # Calculate date range for month
        start_date = date(year, month_num, 1)
        if month_num == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month_num + 1, 1) - timedelta(days=1)

        context['student'] = student
        context['selected_month'] = month
        context['attendance_records'] = ParentAttendanceService.get_attendance_history(
            student, start_date, end_date
        )
        context['stats'] = ParentAttendanceService.get_attendance_stats(student, month)

        # Generate available months (last 12 months)
        today = timezone.now().date()
        months = []
        for i in range(12):
            m = today.replace(day=1) - timedelta(days=i * 30)
            months.append(m.strftime('%Y-%m'))
        context['available_months'] = months

        # Children for selector
        context['children'] = ParentDashboardService.get_children(self.request.user)

        return context


class ParentInvoicesView(LoginRequiredMixin, ParentAccessMixin, HTMXMixin, TemplateView):
    """View invoices for a student."""

    template_name = 'parent_panel/invoices/list.html'
    partial_template_name = 'parent_panel/invoices/partials/_invoices_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.request.current_student

        context['student'] = student
        context['invoices'] = ParentInvoiceService.get_invoices(student)
        context['summary'] = ParentInvoiceService.get_invoice_summary(student)

        # Children for selector
        context['children'] = ParentDashboardService.get_children(self.request.user)

        return context


class ParentTutorsView(LoginRequiredMixin, ParentAccessMixin, HTMXMixin, TemplateView):
    """View tutors teaching a student."""

    template_name = 'parent_panel/tutors/list.html'
    partial_template_name = 'parent_panel/tutors/partials/_tutors_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.request.current_student

        context['student'] = student
        context['tutors'] = ParentTutorService.get_student_tutors(student)

        # Children for selector
        context['children'] = ParentDashboardService.get_children(self.request.user)

        return context


class ParentCalendarView(LoginRequiredMixin, ParentAccessMixin, HTMXMixin, TemplateView):
    """Calendar view for parent portal."""

    template_name = 'parent_panel/calendar.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.request.current_student

        context['student'] = student
        context['children'] = ParentDashboardService.get_children(self.request.user)

        return context


class ParentCalendarEventsView(LoginRequiredMixin, ParentAccessMixin, View):
    """API endpoint for calendar events."""

    def get(self, request, *args, **kwargs):
        student = request.current_student

        start = request.GET.get('start')
        end = request.GET.get('end')

        from datetime import datetime

        from apps.lessons.models import LessonStudent

        start_date = datetime.fromisoformat(start.replace('Z', '+00:00'))
        end_date = datetime.fromisoformat(end.replace('Z', '+00:00'))

        lessons = LessonStudent.objects.filter(
            student=student,
            lesson__start_time__gte=start_date,
            lesson__start_time__lte=end_date,
        ).select_related('lesson', 'lesson__subject', 'lesson__tutor')

        events = []
        for ls in lessons:
            lesson = ls.lesson
            color = '#3B82F6'  # blue
            if lesson.status == 'completed':
                color = '#10B981'  # green
            elif lesson.status == 'cancelled':
                color = '#EF4444'  # red

            events.append(
                {
                    'id': str(lesson.id),
                    'title': lesson.subject.name if lesson.subject else 'Lekcja',
                    'start': lesson.start_time.isoformat(),
                    'end': lesson.end_time.isoformat(),
                    'color': color,
                    'extendedProps': {
                        'tutor': f'{lesson.tutor.first_name} {lesson.tutor.last_name}',
                        'status': lesson.status,
                        'attendance': ls.attendance_status,
                    },
                }
            )

        return JsonResponse(events, safe=False)


class ParentProgressView(LoginRequiredMixin, ParentAccessMixin, HTMXMixin, TemplateView):
    """View student progress and achievements."""

    template_name = 'parent_panel/progress/index.html'
    partial_template_name = 'parent_panel/progress/partials/_progress_content.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.request.current_student

        context['student'] = student
        context['stats'] = ParentDashboardService.get_student_stats(student)

        # Get progress by subject
        from apps.lessons.models import LessonStudent

        subjects_data = (
            LessonStudent.objects.filter(student=student)
            .values('lesson__subject__name', 'lesson__subject__color')
            .annotate(
                total_lessons=models.Count('id'),
                completed_lessons=models.Count(
                    'id', filter=models.Q(lesson__status='completed')
                ),
            )
            .order_by('lesson__subject__name')
        )

        subjects = []
        for s in subjects_data:
            if s['lesson__subject__name']:
                subjects.append(
                    {
                        'name': s['lesson__subject__name'],
                        'color': s['lesson__subject__color'] or '#6B7280',
                        'total_lessons': s['total_lessons'],
                        'completed_lessons': s['completed_lessons'],
                    }
                )
        context['subjects'] = subjects

        # Children for selector
        context['children'] = ParentDashboardService.get_children(self.request.user)

        return context
