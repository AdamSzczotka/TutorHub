from datetime import timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views import View
from django.views.generic import ListView, TemplateView

from apps.core.mixins import AdminRequiredMixin, HTMXMixin, StudentRequiredMixin
from apps.lessons.models import Lesson

from .models import CancellationRequest, CancellationStatus, MakeupLesson, MakeupStatus
from .services import cancellation_service, expiration_service, makeup_service


# Student Views
class CancellationRequestFormView(LoginRequiredMixin, HTMXMixin, TemplateView):
    """Display cancellation request form for a lesson."""

    template_name = 'cancellations/request_form.html'
    partial_template_name = 'cancellations/partials/_request_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lesson_id = self.kwargs.get('lesson_id')
        lesson = get_object_or_404(Lesson, id=lesson_id)

        validation = cancellation_service.validate_24h_rule(lesson)

        context['lesson'] = lesson
        context['can_cancel'] = validation['valid']
        context['hours_until'] = validation['hours_until']

        return context


class CreateCancellationRequestView(LoginRequiredMixin, View):
    """Create a new cancellation request."""

    def post(self, request, lesson_id):
        lesson = get_object_or_404(Lesson, id=lesson_id)
        reason = request.POST.get('reason', '')

        try:
            cancellation_service.create_request(
                lesson=lesson,
                student=request.user,
                reason=reason,
            )

            return HttpResponse(
                '''<div class="alert alert-success">
                    Prosba o anulowanie zostala wyslana. Administrator otrzyma powiadomienie.
                </div>''',
                headers={'HX-Trigger': 'cancellationCreated'},
            )

        except Exception as e:
            return HttpResponse(
                f'<div class="alert alert-error">{str(e)}</div>',
                status=400,
            )


class StudentCancellationsView(LoginRequiredMixin, HTMXMixin, ListView):
    """Display student's cancellation requests."""

    template_name = 'cancellations/student_list.html'
    partial_template_name = 'cancellations/partials/_student_list.html'
    context_object_name = 'requests'

    def get_queryset(self):
        return (
            CancellationRequest.objects.filter(student=self.request.user)
            .select_related('lesson', 'lesson__subject', 'lesson__tutor')
            .order_by('-request_date')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stats'] = cancellation_service.get_student_stats(self.request.user)
        context['pending_makeups'] = cancellation_service.get_pending_makeups(
            self.request.user
        )
        return context


# Admin Views
class AdminCancellationQueueView(
    LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, ListView
):
    """Admin view for pending cancellation requests."""

    template_name = 'admin_panel/cancellations/queue.html'
    partial_template_name = 'admin_panel/cancellations/partials/_queue_list.html'
    context_object_name = 'requests'

    def get_queryset(self):
        status = self.request.GET.get('status', 'pending')
        return (
            CancellationRequest.objects.filter(status=status)
            .select_related(
                'lesson',
                'lesson__subject',
                'lesson__tutor',
                'student',
            )
            .order_by('-request_date')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_status'] = self.request.GET.get('status', 'pending')
        context['pending_count'] = CancellationRequest.objects.filter(
            status=CancellationStatus.PENDING
        ).count()
        return context


class ReviewCancellationView(LoginRequiredMixin, AdminRequiredMixin, View):
    """Approve or reject a cancellation request."""

    def post(self, request, request_id):
        cancellation_request = get_object_or_404(CancellationRequest, id=request_id)
        action = request.POST.get('action')
        notes = request.POST.get('notes', '')

        try:
            if action == 'APPROVE':
                cancellation_service.approve_request(
                    cancellation_request,
                    admin=request.user,
                    notes=notes,
                )
                message = 'Prosba zostala zaakceptowana.'
            elif action == 'REJECT':
                if not notes:
                    return HttpResponse(
                        '<div class="alert alert-error">Podaj powod odrzucenia.</div>',
                        status=400,
                    )
                cancellation_service.reject_request(
                    cancellation_request,
                    admin=request.user,
                    reason=notes,
                )
                message = 'Prosba zostala odrzucona.'
            else:
                return HttpResponse(
                    '<div class="alert alert-error">Nieprawidlowa akcja.</div>',
                    status=400,
                )

            return HttpResponse(
                f'<div class="alert alert-success">{message}</div>',
                headers={'HX-Trigger': 'cancellationReviewed'},
            )

        except Exception as e:
            return HttpResponse(
                f'<div class="alert alert-error">{str(e)}</div>',
                status=400,
            )


class ReviewFormView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    """Display review form for a cancellation request."""

    template_name = 'admin_panel/cancellations/partials/_review_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request_id = self.kwargs.get('request_id')
        context['cancellation'] = get_object_or_404(CancellationRequest, id=request_id)
        return context


# Makeup Lessons - Student Views
class MakeupLessonsListView(LoginRequiredMixin, HTMXMixin, ListView):
    """Display student's makeup lessons."""

    template_name = 'cancellations/makeup/list.html'
    partial_template_name = 'cancellations/makeup/partials/_list.html'
    context_object_name = 'makeup_lessons'

    def get_queryset(self):
        status = self.request.GET.get('status', MakeupStatus.PENDING)
        return makeup_service.get_student_makeup_lessons(
            self.request.user,
            status=status if status != 'ALL' else None,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_status'] = self.request.GET.get('status', MakeupStatus.PENDING)

        # Add countdown info for each lesson
        for lesson in context['makeup_lessons']:
            lesson.countdown = makeup_service.get_countdown_info(lesson)

        # Count expiring lessons
        context['expiring_count'] = MakeupLesson.objects.filter(
            student=self.request.user,
            status=MakeupStatus.PENDING,
            expires_at__lte=timezone.now() + timedelta(days=7),
        ).count()

        return context


class RescheduleFormView(LoginRequiredMixin, HTMXMixin, TemplateView):
    """Display reschedule form with available slots."""

    template_name = 'cancellations/makeup/reschedule.html'
    partial_template_name = 'cancellations/makeup/partials/_reschedule_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        makeup_id = self.kwargs.get('makeup_id')
        makeup_lesson = get_object_or_404(
            MakeupLesson, id=makeup_id, student=self.request.user
        )

        context['makeup_lesson'] = makeup_lesson
        context['countdown'] = makeup_service.get_countdown_info(makeup_lesson)
        context['available_slots'] = makeup_service.get_available_slots(makeup_lesson)

        return context


class ScheduleMakeupView(LoginRequiredMixin, View):
    """Schedule a makeup lesson."""

    def post(self, request, makeup_id):
        makeup_lesson = get_object_or_404(MakeupLesson, id=makeup_id)
        new_lesson_id = request.POST.get('new_lesson_id')

        if not new_lesson_id:
            return HttpResponse(
                '<div class="alert alert-error">Wybierz termin zajec.</div>',
                status=400,
            )

        new_lesson = get_object_or_404(Lesson, id=new_lesson_id)

        try:
            makeup_service.schedule_makeup(makeup_lesson, new_lesson, request.user)

            return HttpResponse(
                '''<div class="alert alert-success">
                    Zajecia zastepcze zostaly pomyslnie zaplanowane.
                </div>''',
                headers={'HX-Trigger': 'makeupScheduled'},
            )

        except Exception as e:
            return HttpResponse(
                f'<div class="alert alert-error">{str(e)}</div>',
                status=400,
            )


# Makeup Lessons - Admin Views
class AdminMakeupListView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, ListView):
    """Admin view for all makeup lessons."""

    template_name = 'admin_panel/makeup/list.html'
    partial_template_name = 'admin_panel/makeup/partials/_list.html'
    context_object_name = 'makeup_lessons'

    def get_queryset(self):
        status = self.request.GET.get('status')
        queryset = MakeupLesson.objects.select_related(
            'student',
            'original_lesson',
            'original_lesson__subject',
            'new_lesson',
            'new_lesson__subject',
        )

        if status:
            queryset = queryset.filter(status=status)

        return queryset.order_by('expires_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stats'] = expiration_service.get_statistics()
        context['current_status'] = self.request.GET.get('status', '')

        # Add countdown info
        for lesson in context['makeup_lessons']:
            lesson.countdown = makeup_service.get_countdown_info(lesson)

        return context


class ExtendDeadlineFormView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    """Display extend deadline form."""

    template_name = 'admin_panel/makeup/partials/_extend_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        makeup_id = self.kwargs.get('makeup_id')
        context['makeup_lesson'] = get_object_or_404(MakeupLesson, id=makeup_id)
        return context


class ExtendDeadlineView(LoginRequiredMixin, AdminRequiredMixin, View):
    """Extend makeup lesson deadline."""

    def post(self, request, makeup_id):
        makeup_lesson = get_object_or_404(MakeupLesson, id=makeup_id)
        new_expires_at = request.POST.get('new_expires_at')
        reason = request.POST.get('reason', '')

        if not new_expires_at or not reason:
            return HttpResponse(
                '<div class="alert alert-error">Wypelnij wszystkie pola.</div>',
                status=400,
            )

        from datetime import datetime

        try:
            new_expires_at = datetime.fromisoformat(new_expires_at)
            new_expires_at = timezone.make_aware(new_expires_at)
        except ValueError:
            return HttpResponse(
                '<div class="alert alert-error">Nieprawidlowy format daty.</div>',
                status=400,
            )

        try:
            makeup_service.extend_deadline(
                makeup_lesson,
                new_expires_at,
                reason,
                request.user,
            )

            return HttpResponse(
                '<div class="alert alert-success">Termin zostal przedluzony.</div>',
                headers={'HX-Trigger': 'deadlineExtended'},
            )

        except Exception as e:
            return HttpResponse(
                f'<div class="alert alert-error">{str(e)}</div>',
                status=400,
            )


class MakeupStatisticsView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    """Display makeup lesson statistics."""

    template_name = 'admin_panel/makeup/statistics.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stats'] = expiration_service.get_statistics()
        return context
