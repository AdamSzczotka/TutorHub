"""Views for student portal."""

from datetime import timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views import View
from django.views.generic import DetailView, TemplateView

from apps.cancellations.models import CancellationRequest, MakeupLesson
from apps.core.mixins import HTMXMixin, StudentRequiredMixin
from apps.lessons.models import Lesson, LessonStudent

from .services import (
    StudentCancellationService,
    StudentDashboardService,
    StudentProgressService,
)


class StudentDashboardView(LoginRequiredMixin, StudentRequiredMixin, TemplateView):
    """Student dashboard with personalized widgets."""

    template_name = 'student_panel/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.request.user

        context['stats'] = StudentDashboardService.get_dashboard_stats(student)
        context['today_lessons'] = StudentDashboardService.get_today_lessons(student)
        context['upcoming_lessons'] = StudentDashboardService.get_upcoming_lessons(
            student
        )
        context['makeup_lessons'] = StudentDashboardService.get_makeup_lessons(student)
        context['recent_progress'] = StudentDashboardService.get_recent_progress(
            student
        )
        context['today'] = timezone.now()

        return context


class StudentCalendarView(LoginRequiredMixin, StudentRequiredMixin, TemplateView):
    """Student calendar page with FullCalendar."""

    template_name = 'student_panel/calendar.html'


class StudentCalendarEventsView(LoginRequiredMixin, StudentRequiredMixin, View):
    """API endpoint for student calendar events."""

    def get(self, request):
        student = request.user
        start = request.GET.get('start')
        end = request.GET.get('end')

        lessons = LessonStudent.objects.filter(student=student).select_related(
            'lesson', 'lesson__subject', 'lesson__tutor', 'lesson__room'
        )

        if start:
            lessons = lessons.filter(lesson__start_time__gte=start)
        if end:
            lessons = lessons.filter(lesson__end_time__lte=end)

        events = []
        for ls in lessons:
            lesson = ls.lesson
            color = self._get_status_color(lesson.status)

            events.append(
                {
                    'id': str(lesson.id),
                    'title': lesson.title,
                    'start': lesson.start_time.isoformat(),
                    'end': lesson.end_time.isoformat(),
                    'backgroundColor': color,
                    'borderColor': color,
                    'extendedProps': {
                        'subject': lesson.subject.name if lesson.subject else '',
                        'tutor': lesson.tutor.get_full_name() if lesson.tutor else '',
                        'room': lesson.room.name if lesson.room else 'Online',
                        'status': lesson.status,
                    },
                }
            )

        return JsonResponse(events, safe=False)

    @staticmethod
    def _get_status_color(status: str) -> str:
        colors = {
            'scheduled': '#3B82F6',  # blue
            'ongoing': '#10B981',  # green
            'completed': '#6B7280',  # gray
            'cancelled': '#EF4444',  # red
        }
        return colors.get(status, '#3B82F6')


class StudentLessonDetailView(
    LoginRequiredMixin, StudentRequiredMixin, HTMXMixin, DetailView
):
    """Student lesson detail modal."""

    model = Lesson
    template_name = 'student_panel/lessons/partials/_lesson_detail.html'
    context_object_name = 'lesson'

    def get_queryset(self):
        return Lesson.objects.filter(
            lesson_students__student=self.request.user
        ).select_related('tutor', 'subject', 'room')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lesson = self.object

        # Check if can cancel
        can_cancel, _ = StudentCancellationService.can_cancel_lesson(
            self.request.user, lesson
        )
        context['can_cancel'] = can_cancel and lesson.status == 'scheduled'
        context['hours_until'] = (
            lesson.start_time - timezone.now()
        ).total_seconds() / 3600

        return context


class CancellationRequestListView(
    LoginRequiredMixin, StudentRequiredMixin, HTMXMixin, TemplateView
):
    """Student cancellation requests page."""

    template_name = 'student_panel/cancellations/list.html'
    partial_template_name = 'student_panel/cancellations/partials/_request_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.request.user

        # Get cancellable lessons
        context['upcoming_lessons'] = StudentCancellationService.get_cancellable_lessons(
            student
        )

        # Get existing requests
        context['requests'] = StudentCancellationService.get_student_requests(student)

        # Get limit info
        context['limit_info'] = StudentCancellationService.get_cancellation_limit(
            student
        )

        # Pre-selected lesson (if from calendar)
        event_id = self.request.GET.get('eventId')
        if event_id:
            context['preselected_lesson_id'] = event_id

        return context


class CancellationRequestCreateView(LoginRequiredMixin, StudentRequiredMixin, View):
    """Create cancellation request via HTMX."""

    def post(self, request):
        student = request.user
        lesson_id = request.POST.get('lesson')
        reason = request.POST.get('reason', '')

        if not lesson_id:
            return HttpResponse(
                '<div class="alert alert-error">Wybierz zajęcia do anulowania</div>',
                status=400,
            )

        if len(reason) < 10:
            return HttpResponse(
                '<div class="alert alert-error">Powód musi zawierać minimum 10 znaków</div>',
                status=400,
            )

        lesson = get_object_or_404(Lesson, id=lesson_id)

        try:
            StudentCancellationService.create_cancellation_request(
                student=student,
                lesson=lesson,
                reason=reason,
            )

            return HttpResponse(
                '<div class="alert alert-success">'
                'Wniosek o anulowanie został wysłany. Administrator rozpatrzy go wkrótce.'
                '</div>',
                headers={'HX-Trigger': 'cancellationCreated'},
            )
        except ValueError as e:
            return HttpResponse(
                f'<div class="alert alert-error">{str(e)}</div>',
                status=400,
            )


class MakeupLessonsListView(
    LoginRequiredMixin, StudentRequiredMixin, HTMXMixin, TemplateView
):
    """Student makeup lessons tracker."""

    template_name = 'student_panel/makeup/list.html'
    partial_template_name = 'student_panel/makeup/partials/_makeup_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.request.user
        today = timezone.now()

        makeup_lessons = (
            MakeupLesson.objects.filter(student=student)
            .select_related(
                'original_lesson', 'original_lesson__subject', 'original_lesson__tutor'
            )
            .order_by('expires_at')
        )

        # Add computed fields
        makeup_list = []
        for makeup in makeup_lessons:
            days_left = (makeup.expires_at - today).days
            makeup.days_left = max(0, days_left)
            makeup.progress = min(100, max(0, ((30 - days_left) / 30) * 100))
            makeup.is_expiring_soon = 0 < days_left <= 7
            makeup.has_expired = days_left < 0
            makeup_list.append(makeup)

        context['makeup_lessons'] = makeup_list
        context['expiring_soon_count'] = sum(
            1 for m in makeup_list if m.is_expiring_soon
        )

        return context


class StudentProgressView(
    LoginRequiredMixin, StudentRequiredMixin, HTMXMixin, TemplateView
):
    """Student progress and achievements page."""

    template_name = 'student_panel/progress/index.html'
    partial_template_name = 'student_panel/progress/partials/_progress_content.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.request.user

        context['stats'] = StudentProgressService.get_progress_stats(student)
        context['subjects'] = StudentProgressService.get_subject_progress(student)
        context['achievements'] = StudentProgressService.get_achievements(student)

        return context
