# Phase 6 - Sprint 6.2: Makeup Lessons System (Django)

## Tasks 082-086: Makeup Lesson Tracking & Rescheduling

> **Duration**: Week 10 (Second half of Phase 6)
> **Goal**: Complete makeup lessons system with 30-day expiration and rescheduling
> **Dependencies**: Sprint 6.1 completed (Cancellation system)

---

## SPRINT OVERVIEW

| Task ID | Description                                | Priority | Dependencies |
| ------- | ------------------------------------------ | -------- | ------------ |
| 082     | Makeup lessons tracking (30-day countdown) | Critical | Sprint 6.1   |
| 083     | Rescheduling interface                     | Critical | Task 082     |
| 084     | Expiration handling                        | Critical | Task 083     |
| 085     | Admin extension feature                    | High     | Task 084     |
| 086     | Makeup statistics                          | High     | Task 085     |

---

## MAKEUP LESSON SERVICE

**File**: `apps/cancellations/services.py` (rozszerzenie)

```python
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
from datetime import timedelta
from .models import MakeupLesson


class MakeupLessonService:
    """Service for handling makeup lessons."""

    def get_student_makeup_lessons(self, student, status=None):
        """Get makeup lessons for a student."""
        queryset = MakeupLesson.objects.filter(
            student=student
        ).select_related(
            'original_lesson',
            'original_lesson__subject',
            'original_lesson__tutor',
            'new_lesson',
            'new_lesson__subject',
            'new_lesson__tutor'
        )

        if status:
            queryset = queryset.filter(status=status)

        return queryset.order_by('expires_at')

    def get_countdown_info(self, makeup_lesson):
        """Calculate countdown information for a makeup lesson."""
        now = timezone.now()
        expires_at = makeup_lesson.expires_at

        if expires_at < now:
            return {
                'text': 'Wygasło',
                'variant': 'expired',
                'progress': 0,
                'days_left': 0,
                'hours_left': 0
            }

        delta = expires_at - now
        days_left = delta.days
        hours_left = delta.seconds // 3600

        # Calculate progress (percentage of 30 days remaining)
        total_seconds = 30 * 24 * 3600
        remaining_seconds = delta.total_seconds()
        progress = (remaining_seconds / total_seconds) * 100

        if days_left <= 7:
            variant = 'urgent'
        else:
            variant = 'normal'

        return {
            'text': f'{days_left}d {hours_left}h' if days_left <= 7 else f'{days_left} dni',
            'variant': variant,
            'progress': min(100, max(0, progress)),
            'days_left': days_left,
            'hours_left': hours_left
        }

    def get_available_slots(self, makeup_lesson):
        """Get available lesson slots for makeup."""
        from apps.lessons.models import Lesson

        original = makeup_lesson.original_lesson

        # Find future lessons with same subject/level/tutor
        available = Lesson.objects.filter(
            subject=original.subject,
            tutor=original.tutor,
            start_time__gte=timezone.now(),
            status='SCHEDULED'
        ).exclude(
            students=makeup_lesson.student  # Student not already enrolled
        ).select_related(
            'subject', 'tutor', 'room'
        ).annotate(
            student_count=models.Count('students')
        ).order_by('start_time')[:20]

        # Filter by capacity
        slots = []
        for lesson in available:
            if not lesson.is_group_lesson:
                # Individual lesson - must be empty
                if lesson.student_count == 0:
                    slots.append(lesson)
            else:
                # Group lesson - check capacity
                if lesson.max_participants and lesson.student_count < lesson.max_participants:
                    slots.append(lesson)

        return slots

    @transaction.atomic
    def schedule_makeup(self, makeup_lesson, new_lesson, user):
        """Schedule a makeup lesson."""
        # Validate not expired
        if makeup_lesson.expires_at < timezone.now():
            raise ValidationError("Termin odrobienia zajęć wygasł.")

        # Validate status
        if makeup_lesson.status != 'PENDING':
            raise ValidationError("Zajęcia zostały już zaplanowane.")

        # Validate permission
        if makeup_lesson.student != user and not user.is_staff:
            raise ValidationError("Brak uprawnień.")

        # Check slot availability
        if new_lesson.is_group_lesson:
            if new_lesson.max_participants:
                current_count = new_lesson.students.count()
                if current_count >= new_lesson.max_participants:
                    raise ValidationError("Brak wolnych miejsc na tych zajęciach.")
        else:
            if new_lesson.students.exists():
                raise ValidationError("Te zajęcia są już zajęte.")

        # Assign student to new lesson
        new_lesson.students.add(makeup_lesson.student)

        # Update makeup lesson
        makeup_lesson.new_lesson = new_lesson
        makeup_lesson.status = 'SCHEDULED'
        makeup_lesson.save()

        # Send notification
        self._notify_makeup_scheduled(makeup_lesson)

        return makeup_lesson

    @transaction.atomic
    def extend_deadline(self, makeup_lesson, new_expires_at, reason, admin):
        """Extend makeup lesson deadline (admin only)."""
        if new_expires_at <= makeup_lesson.expires_at:
            raise ValidationError("Nowy termin musi być późniejszy niż obecny.")

        old_expires = makeup_lesson.expires_at

        makeup_lesson.expires_at = new_expires_at
        makeup_lesson.notes = (
            f"{makeup_lesson.notes or ''}\n\n"
            f"Przedłużono do {new_expires_at.strftime('%d.%m.%Y %H:%M')}. "
            f"Powód: {reason}"
        )
        makeup_lesson.save()

        # Notify student
        self._notify_deadline_extended(makeup_lesson, old_expires, new_expires_at, reason)

        return makeup_lesson

    def _notify_makeup_scheduled(self, makeup_lesson):
        """Notify student about scheduled makeup lesson."""
        from apps.notifications.services import notification_service

        notification_service.create(
            user=makeup_lesson.student,
            notification_type='MAKEUP_SCHEDULED',
            title='Zajęcia zastępcze umówione',
            message=f'Zajęcia zastępcze zostały zaplanowane na {makeup_lesson.new_lesson.start_time.strftime("%d.%m.%Y, %H:%M")}'
        )

    def _notify_deadline_extended(self, makeup_lesson, old_expires, new_expires, reason):
        """Notify student about extended deadline."""
        from apps.notifications.services import notification_service

        notification_service.create(
            user=makeup_lesson.student,
            notification_type='MAKEUP_EXTENDED',
            title='Termin odrobienia przedłużony',
            message=f'Termin odrobienia zajęć "{makeup_lesson.original_lesson.title}" został przedłużony do {new_expires.strftime("%d.%m.%Y, %H:%M")}. Powód: {reason}'
        )


makeup_service = MakeupLessonService()
```

---

## EXPIRATION SERVICE

**File**: `apps/cancellations/services.py` (rozszerzenie)

```python
class MakeupExpirationService:
    """Service for handling makeup lesson expiration."""

    def expire_past_deadline(self):
        """Auto-expire makeup lessons past deadline."""
        from apps.notifications.services import notification_service

        expired_lessons = MakeupLesson.objects.filter(
            status='PENDING',
            expires_at__lt=timezone.now()
        ).select_related('original_lesson', 'student')

        count = 0
        for lesson in expired_lessons:
            lesson.status = 'EXPIRED'
            lesson.save()

            # Notify student
            notification_service.create(
                user=lesson.student,
                notification_type='MAKEUP_EXPIRED',
                title='Zajęcia zastępcze wygasły',
                message=f'Termin odrobienia zajęć "{lesson.original_lesson.title}" wygasł. Skontaktuj się z administratorem w sprawie przedłużenia.'
            )

            count += 1

        return count

    def send_expiration_warnings(self):
        """Send warnings for lessons expiring in 7 days."""
        from apps.notifications.models import Notification

        seven_days = timezone.now() + timedelta(days=7)

        expiring_lessons = MakeupLesson.objects.filter(
            status='PENDING',
            expires_at__gte=timezone.now(),
            expires_at__lte=seven_days
        ).select_related('original_lesson', 'student')

        count = 0
        for lesson in expiring_lessons:
            # Check if warning already sent today
            today = timezone.now().date()
            existing = Notification.objects.filter(
                user=lesson.student,
                notification_type='MAKEUP_EXPIRING_SOON',
                created_at__date=today
            ).exists()

            if existing:
                continue

            days_left = (lesson.expires_at - timezone.now()).days

            from apps.notifications.services import notification_service
            notification_service.create(
                user=lesson.student,
                notification_type='MAKEUP_EXPIRING_SOON',
                title='Zajęcia zastępcze wkrótce wygasną!',
                message=f'Zostało tylko {days_left} dni na umówienie zajęć zastępczych za "{lesson.original_lesson.title}". Umów termin jak najszybciej!'
            )

            count += 1

        return count

    def get_statistics(self):
        """Get makeup lesson statistics."""
        pending = MakeupLesson.objects.filter(status='PENDING').count()
        scheduled = MakeupLesson.objects.filter(status='SCHEDULED').count()
        completed = MakeupLesson.objects.filter(status='COMPLETED').count()
        expired = MakeupLesson.objects.filter(status='EXPIRED').count()

        total = pending + scheduled + completed + expired

        if completed + expired > 0:
            utilization_rate = (completed / (completed + expired)) * 100
        else:
            utilization_rate = 0

        return {
            'pending': pending,
            'scheduled': scheduled,
            'completed': completed,
            'expired': expired,
            'total': total,
            'utilization_rate': round(utilization_rate)
        }


expiration_service = MakeupExpirationService()
```

---

## MAKEUP LESSON VIEWS

**File**: `apps/cancellations/views.py` (rozszerzenie)

```python
from django.views.generic import ListView, TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from apps.core.mixins import AdminRequiredMixin, HTMXMixin
from apps.lessons.models import Lesson
from .models import MakeupLesson
from .services import makeup_service, expiration_service


class MakeupLessonsListView(LoginRequiredMixin, HTMXMixin, ListView):
    """Display student's makeup lessons."""
    template_name = 'cancellations/makeup/list.html'
    partial_template_name = 'cancellations/makeup/partials/_list.html'
    context_object_name = 'makeup_lessons'

    def get_queryset(self):
        status = self.request.GET.get('status', 'PENDING')
        return makeup_service.get_student_makeup_lessons(
            self.request.user,
            status=status if status != 'ALL' else None
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_status'] = self.request.GET.get('status', 'PENDING')

        # Add countdown info for each lesson
        for lesson in context['makeup_lessons']:
            lesson.countdown = makeup_service.get_countdown_info(lesson)

        # Count expiring lessons
        context['expiring_count'] = MakeupLesson.objects.filter(
            student=self.request.user,
            status='PENDING',
            expires_at__lte=timezone.now() + timedelta(days=7)
        ).count()

        return context


class RescheduleFormView(LoginRequiredMixin, HTMXMixin, TemplateView):
    """Display reschedule form with available slots."""
    template_name = 'cancellations/makeup/reschedule.html'
    partial_template_name = 'cancellations/makeup/partials/_reschedule_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        makeup_id = self.kwargs.get('makeup_id')
        makeup_lesson = get_object_or_404(MakeupLesson, id=makeup_id, student=self.request.user)

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
                '<div class="alert alert-error">Wybierz termin zajęć.</div>',
                status=400
            )

        new_lesson = get_object_or_404(Lesson, id=new_lesson_id)

        try:
            makeup_service.schedule_makeup(
                makeup_lesson,
                new_lesson,
                request.user
            )

            return HttpResponse(
                '''<div class="alert alert-success">
                    Zajęcia zastępcze zostały pomyślnie zaplanowane.
                </div>''',
                headers={'HX-Trigger': 'makeupScheduled'}
            )

        except Exception as e:
            return HttpResponse(
                f'<div class="alert alert-error">{str(e)}</div>',
                status=400
            )


# Admin Views
class AdminMakeupListView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, ListView):
    """Admin view for all makeup lessons."""
    template_name = 'admin_panel/makeup/list.html'
    partial_template_name = 'admin_panel/makeup/partials/_list.html'
    context_object_name = 'makeup_lessons'

    def get_queryset(self):
        status = self.request.GET.get('status')
        queryset = MakeupLesson.objects.select_related(
            'student', 'original_lesson', 'original_lesson__subject',
            'new_lesson', 'new_lesson__subject'
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
                '<div class="alert alert-error">Wypełnij wszystkie pola.</div>',
                status=400
            )

        from datetime import datetime
        try:
            new_expires_at = datetime.fromisoformat(new_expires_at)
            new_expires_at = timezone.make_aware(new_expires_at)
        except ValueError:
            return HttpResponse(
                '<div class="alert alert-error">Nieprawidłowy format daty.</div>',
                status=400
            )

        try:
            makeup_service.extend_deadline(
                makeup_lesson,
                new_expires_at,
                reason,
                request.user
            )

            return HttpResponse(
                '<div class="alert alert-success">Termin został przedłużony.</div>',
                headers={'HX-Trigger': 'deadlineExtended'}
            )

        except Exception as e:
            return HttpResponse(
                f'<div class="alert alert-error">{str(e)}</div>',
                status=400
            )


class MakeupStatisticsView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    """Display makeup lesson statistics."""
    template_name = 'admin_panel/makeup/statistics.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stats'] = expiration_service.get_statistics()
        return context
```

---

## MAKEUP LESSON TEMPLATES

**File**: `templates/cancellations/makeup/list.html`

```html
{% extends "base.html" %}

{% block content %}
<div class="space-y-6">
    <div class="flex items-center justify-between">
        <div>
            <h1 class="text-2xl font-bold">Zajęcia do odrobienia</h1>
            <p class="text-base-content/70">Zarządzaj swoimi zajęciami zastępczymi</p>
        </div>

        {% if expiring_count > 0 %}
        <span class="badge badge-warning badge-lg gap-1">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                      d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
            </svg>
            {{ expiring_count }} wkrótce wygasają
        </span>
        {% endif %}
    </div>

    <!-- Status Tabs -->
    <div class="tabs tabs-boxed">
        <a class="tab {% if current_status == 'PENDING' %}tab-active{% endif %}"
           hx-get="{% url 'cancellations:makeup_list' %}?status=PENDING"
           hx-target="#makeup-list"
           hx-swap="innerHTML">
            Do odrobienia
        </a>
        <a class="tab {% if current_status == 'SCHEDULED' %}tab-active{% endif %}"
           hx-get="{% url 'cancellations:makeup_list' %}?status=SCHEDULED"
           hx-target="#makeup-list"
           hx-swap="innerHTML">
            Zaplanowane
        </a>
        <a class="tab {% if current_status == 'COMPLETED' %}tab-active{% endif %}"
           hx-get="{% url 'cancellations:makeup_list' %}?status=COMPLETED"
           hx-target="#makeup-list"
           hx-swap="innerHTML">
            Odrobione
        </a>
        <a class="tab {% if current_status == 'EXPIRED' %}tab-active{% endif %}"
           hx-get="{% url 'cancellations:makeup_list' %}?status=EXPIRED"
           hx-target="#makeup-list"
           hx-swap="innerHTML">
            Wygasłe
        </a>
    </div>

    <div id="makeup-list"
         hx-get="{% url 'cancellations:makeup_list' %}?status={{ current_status }}"
         hx-trigger="makeupScheduled from:body"
         hx-swap="innerHTML">
        {% include "cancellations/makeup/partials/_list.html" %}
    </div>
</div>

<!-- Reschedule Modal -->
<dialog id="reschedule-modal" class="modal">
    <div class="modal-box max-w-4xl max-h-[90vh]">
        <div id="reschedule-modal-content"></div>
    </div>
    <form method="dialog" class="modal-backdrop">
        <button>close</button>
    </form>
</dialog>
{% endblock %}
```

**File**: `templates/cancellations/makeup/partials/_list.html`

```html
{% if makeup_lessons %}
<div class="space-y-4">
    {% for lesson in makeup_lessons %}
    <div class="card bg-base-100 shadow relative overflow-hidden">
        <!-- Progress Bar -->
        {% if lesson.countdown.variant != 'expired' %}
        <div class="absolute top-0 left-0 right-0 h-1 bg-base-300">
            <div class="h-full {% if lesson.countdown.variant == 'urgent' %}bg-warning{% else %}bg-primary{% endif %}"
                 style="width: {{ lesson.countdown.progress }}%"></div>
        </div>
        {% endif %}

        <div class="card-body pt-5">
            <div class="flex items-start justify-between">
                <div class="space-y-1">
                    <h3 class="card-title text-lg">{{ lesson.original_lesson.title }}</h3>
                    <div class="flex items-center gap-2 text-sm text-base-content/70">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                  d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/>
                        </svg>
                        Oryginalna data: {{ lesson.original_lesson.start_time|date:"d.m.Y, H:i" }}
                    </div>
                </div>

                {% if lesson.status == 'PENDING' %}
                <span class="badge badge-primary">Do odrobienia</span>
                {% elif lesson.status == 'SCHEDULED' %}
                <span class="badge badge-info">Zaplanowane</span>
                {% elif lesson.status == 'COMPLETED' %}
                <span class="badge badge-success">Odrobione</span>
                {% else %}
                <span class="badge badge-error">Wygasło</span>
                {% endif %}
            </div>

            <!-- Countdown Alert -->
            {% if lesson.status == 'PENDING' %}
                {% if lesson.countdown.variant == 'urgent' %}
                <div class="alert alert-warning mt-4">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
                    </svg>
                    <span>Uwaga! Zostało tylko {{ lesson.countdown.text }} do wygaśnięcia!</span>
                </div>
                {% else %}
                <div class="alert alert-info mt-4">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                              d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                    </svg>
                    <span>Masz {{ lesson.countdown.text }} na umówienie zajęć zastępczych</span>
                </div>
                {% endif %}
            {% endif %}

            <!-- Expiration Details -->
            <div class="bg-base-200 rounded-lg p-4 mt-4 space-y-2">
                <div class="flex items-center justify-between text-sm">
                    <span class="text-base-content/70">Data wygaśnięcia:</span>
                    <span class="font-medium">{{ lesson.expires_at|date:"d.m.Y, H:i" }}</span>
                </div>

                {% if lesson.status == 'PENDING' %}
                <div class="flex items-center justify-between text-sm">
                    <span class="text-base-content/70">Czas pozostały:</span>
                    <span class="font-medium {% if lesson.countdown.variant == 'urgent' %}text-warning{% else %}text-primary{% endif %}">
                        {{ lesson.countdown.text }}
                    </span>
                </div>

                <!-- Progress Bar -->
                <div class="pt-2">
                    <progress class="progress {% if lesson.countdown.variant == 'urgent' %}progress-warning{% else %}progress-primary{% endif %} w-full"
                              value="{{ lesson.countdown.progress }}"
                              max="100"></progress>
                </div>
                {% endif %}

                {% if lesson.new_lesson %}
                <div class="flex items-center justify-between text-sm pt-2 border-t border-base-300 mt-2">
                    <span class="text-base-content/70">Nowy termin:</span>
                    <span class="font-medium text-success">
                        {{ lesson.new_lesson.start_time|date:"d.m.Y, H:i" }}
                    </span>
                </div>
                {% endif %}
            </div>

            {% if lesson.notes %}
            <div class="mt-4">
                <div class="text-sm font-medium mb-1">Notatka:</div>
                <div class="text-sm text-base-content/70 bg-base-200 p-2 rounded">
                    {{ lesson.notes|linebreaks }}
                </div>
            </div>
            {% endif %}

            <!-- Action Button -->
            {% if lesson.status == 'PENDING' %}
            <div class="card-actions justify-end mt-4 pt-4 border-t">
                <button class="btn btn-primary"
                        hx-get="{% url 'cancellations:reschedule_form' lesson.id %}"
                        hx-target="#reschedule-modal-content"
                        onclick="document.getElementById('reschedule-modal').showModal()">
                    Umów zajęcia zastępcze
                </button>
            </div>
            {% endif %}
        </div>
    </div>
    {% endfor %}
</div>
{% else %}
<div class="card bg-base-100 shadow">
    <div class="card-body py-12 text-center">
        <svg class="w-12 h-12 mx-auto mb-4 text-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
        </svg>
        <p class="text-lg font-medium">Brak zajęć do odrobienia</p>
        <p class="text-sm text-base-content/70 mt-2">
            Wszystkie anulowane zajęcia zostały już odrobione lub wygasły
        </p>
    </div>
</div>
{% endif %}
```

**File**: `templates/cancellations/makeup/partials/_reschedule_form.html`

```html
<h3 class="font-bold text-lg mb-4">Umów zajęcia zastępcze</h3>

<!-- Original Lesson Info -->
<div class="bg-info/10 border border-info/30 rounded-lg p-4 mb-4">
    <h4 class="font-semibold text-info-content mb-2">Anulowane zajęcia:</h4>
    <div class="text-sm text-info-content/80 space-y-1">
        <div>{{ makeup_lesson.original_lesson.title }}</div>
        <div>{{ makeup_lesson.original_lesson.start_time|date:"d.m.Y, H:i" }}</div>
        <div>Przedmiot: {{ makeup_lesson.original_lesson.subject.name }}</div>
    </div>
</div>

<!-- Expiration Warning -->
<div class="alert {% if countdown.variant == 'urgent' %}alert-warning{% else %}alert-info{% endif %} mb-4">
    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
    </svg>
    <span>Termin ważności: {{ makeup_lesson.expires_at|date:"d.m.Y, H:i" }}</span>
</div>

<!-- Available Slots -->
<form hx-post="{% url 'cancellations:schedule_makeup' makeup_lesson.id %}"
      hx-target="#reschedule-result"
      hx-swap="innerHTML"
      x-data="{ selectedSlot: '' }">
    {% csrf_token %}

    <input type="hidden" name="new_lesson_id" x-model="selectedSlot">

    <div id="reschedule-result"></div>

    {% if available_slots %}
    <h4 class="font-semibold mb-3">Dostępne terminy ({{ available_slots|length }})</h4>

    <div class="space-y-2 max-h-96 overflow-y-auto">
        {% for slot in available_slots %}
        <div class="border rounded-lg p-4 cursor-pointer transition-all hover:shadow-md"
             :class="selectedSlot === '{{ slot.id }}' ? 'border-primary bg-primary/5 ring-2 ring-primary' : 'border-base-300'"
             @click="selectedSlot = '{{ slot.id }}'">
            <div class="flex items-start justify-between">
                <div class="space-y-1 flex-1">
                    <div class="font-medium">{{ slot.title }}</div>
                    <div class="flex flex-wrap gap-3 text-sm text-base-content/70">
                        <div class="flex items-center gap-1">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                      d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/>
                            </svg>
                            {{ slot.start_time|date:"l, d.m.Y" }}
                        </div>
                        <div class="flex items-center gap-1">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                      d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                            </svg>
                            {{ slot.start_time|time:"H:i" }} - {{ slot.end_time|time:"H:i" }}
                        </div>
                        {% if slot.room %}
                        <div class="flex items-center gap-1">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                      d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/>
                            </svg>
                            {{ slot.room.name }}
                        </div>
                        {% endif %}
                    </div>
                </div>

                {% if slot.is_group_lesson %}
                <span class="badge badge-outline">Grupowe</span>
                {% else %}
                <span class="badge badge-primary badge-outline">Indywidualne</span>
                {% endif %}
            </div>
        </div>
        {% endfor %}
    </div>
    {% else %}
    <div class="text-center py-8 text-base-content/50">
        <p class="font-medium">Brak dostępnych terminów</p>
        <p class="text-sm mt-2">Skontaktuj się z administratorem w celu ustalenia terminu</p>
    </div>
    {% endif %}

    <div class="flex items-center justify-end gap-2 pt-4 mt-4 border-t">
        <button type="button"
                class="btn btn-ghost"
                onclick="document.getElementById('reschedule-modal').close()">
            Anuluj
        </button>
        <button type="submit"
                class="btn btn-primary"
                :disabled="!selectedSlot">
            Potwierdź termin
        </button>
    </div>
</form>
```

---

## ADMIN TEMPLATES

**File**: `templates/admin_panel/makeup/list.html`

```html
{% extends "admin_panel/base.html" %}

{% block content %}
<div class="space-y-6">
    <div class="flex items-center justify-between">
        <div>
            <h1 class="text-2xl font-bold">Zajęcia zastępcze</h1>
            <p class="text-base-content/70">Zarządzaj zajęciami do odrobienia</p>
        </div>

        <a href="{% url 'cancellations:makeup_statistics' %}" class="btn btn-outline">
            <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                      d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
            </svg>
            Statystyki
        </a>
    </div>

    <!-- Statistics Cards -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div class="stat bg-base-100 rounded-box shadow">
            <div class="stat-figure text-primary">
                <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                          d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
            </div>
            <div class="stat-title">Oczekujące</div>
            <div class="stat-value text-primary">{{ stats.pending }}</div>
        </div>

        <div class="stat bg-base-100 rounded-box shadow">
            <div class="stat-figure text-info">
                <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                          d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/>
                </svg>
            </div>
            <div class="stat-title">Zaplanowane</div>
            <div class="stat-value text-info">{{ stats.scheduled }}</div>
        </div>

        <div class="stat bg-base-100 rounded-box shadow">
            <div class="stat-figure text-success">
                <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                          d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
            </div>
            <div class="stat-title">Odrobione</div>
            <div class="stat-value text-success">{{ stats.completed }}</div>
        </div>

        <div class="stat bg-base-100 rounded-box shadow">
            <div class="stat-figure text-error">
                <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                          d="M6 18L18 6M6 6l12 12"/>
                </svg>
            </div>
            <div class="stat-title">Wygasłe</div>
            <div class="stat-value text-error">{{ stats.expired }}</div>
        </div>
    </div>

    <!-- Filter Tabs -->
    <div class="tabs tabs-boxed">
        <a class="tab {% if not current_status %}tab-active{% endif %}"
           hx-get="{% url 'cancellations:admin_makeup_list' %}"
           hx-target="#makeup-list"
           hx-swap="innerHTML">
            Wszystkie
        </a>
        <a class="tab {% if current_status == 'PENDING' %}tab-active{% endif %}"
           hx-get="{% url 'cancellations:admin_makeup_list' %}?status=PENDING"
           hx-target="#makeup-list"
           hx-swap="innerHTML">
            Oczekujące
        </a>
        <a class="tab {% if current_status == 'SCHEDULED' %}tab-active{% endif %}"
           hx-get="{% url 'cancellations:admin_makeup_list' %}?status=SCHEDULED"
           hx-target="#makeup-list"
           hx-swap="innerHTML">
            Zaplanowane
        </a>
        <a class="tab {% if current_status == 'EXPIRED' %}tab-active{% endif %}"
           hx-get="{% url 'cancellations:admin_makeup_list' %}?status=EXPIRED"
           hx-target="#makeup-list"
           hx-swap="innerHTML">
            Wygasłe
        </a>
    </div>

    <div id="makeup-list"
         hx-get="{% url 'cancellations:admin_makeup_list' %}{% if current_status %}?status={{ current_status }}{% endif %}"
         hx-trigger="deadlineExtended from:body"
         hx-swap="innerHTML">
        {% include "admin_panel/makeup/partials/_list.html" %}
    </div>
</div>

<!-- Extend Modal -->
<dialog id="extend-modal" class="modal">
    <div class="modal-box">
        <div id="extend-modal-content"></div>
    </div>
    <form method="dialog" class="modal-backdrop">
        <button>close</button>
    </form>
</dialog>
{% endblock %}
```

**File**: `templates/admin_panel/makeup/partials/_extend_form.html`

```html
<h3 class="font-bold text-lg mb-4">Przedłuż termin odrobienia</h3>

<!-- Current Expiration -->
<div class="alert alert-info mb-4">
    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
    </svg>
    <span>Aktualny termin wygaśnięcia: {{ makeup_lesson.expires_at|date:"d.m.Y, H:i" }}</span>
</div>

<form hx-post="{% url 'cancellations:extend_deadline' makeup_lesson.id %}"
      hx-target="#extend-result"
      hx-swap="innerHTML"
      class="space-y-4">
    {% csrf_token %}

    <div id="extend-result"></div>

    <div class="form-control">
        <label class="label">
            <span class="label-text">Nowy termin wygaśnięcia *</span>
        </label>
        <input type="datetime-local"
               name="new_expires_at"
               class="input input-bordered w-full"
               min="{{ makeup_lesson.expires_at|date:'Y-m-d' }}T00:00"
               required>
    </div>

    <div class="form-control">
        <label class="label">
            <span class="label-text">Powód przedłużenia *</span>
        </label>
        <textarea name="reason"
                  class="textarea textarea-bordered w-full"
                  rows="3"
                  placeholder="Podaj powód przedłużenia terminu (min. 10 znaków)..."
                  minlength="10"
                  required></textarea>
    </div>

    <div class="flex items-center justify-end gap-2 pt-4 border-t">
        <button type="button"
                class="btn btn-ghost"
                onclick="document.getElementById('extend-modal').close()">
            Anuluj
        </button>
        <button type="submit" class="btn btn-primary">
            Przedłuż termin
        </button>
    </div>
</form>
```

---

## CELERY TASKS

**File**: `apps/cancellations/tasks.py` (rozszerzenie)

```python
from celery import shared_task


@shared_task
def expire_makeup_lessons():
    """Daily task to expire past deadline makeup lessons."""
    from .services import expiration_service

    count = expiration_service.expire_past_deadline()
    return f"Expired {count} makeup lessons"


@shared_task
def send_makeup_expiration_warnings():
    """Daily task to send warnings for expiring makeup lessons."""
    from .services import expiration_service

    count = expiration_service.send_expiration_warnings()
    return f"Sent {count} expiration warnings"


# Celery beat schedule in settings.py:
# CELERY_BEAT_SCHEDULE = {
#     'expire-makeup-lessons': {
#         'task': 'apps.cancellations.tasks.expire_makeup_lessons',
#         'schedule': crontab(hour=0, minute=0),  # Every day at midnight
#     },
#     'send-makeup-warnings': {
#         'task': 'apps.cancellations.tasks.send_makeup_expiration_warnings',
#         'schedule': crontab(hour=8, minute=0),  # Every day at 8:00 AM
#     },
# }
```

---

## URL CONFIGURATION

**File**: `apps/cancellations/urls.py` (rozszerzenie)

```python
from django.urls import path
from . import views

app_name = 'cancellations'

urlpatterns = [
    # ... existing urls ...

    # Makeup lessons - Student
    path('makeup/', views.MakeupLessonsListView.as_view(), name='makeup_list'),
    path('makeup/<uuid:makeup_id>/reschedule/', views.RescheduleFormView.as_view(), name='reschedule_form'),
    path('makeup/<uuid:makeup_id>/schedule/', views.ScheduleMakeupView.as_view(), name='schedule_makeup'),

    # Makeup lessons - Admin
    path('admin/makeup/', views.AdminMakeupListView.as_view(), name='admin_makeup_list'),
    path('admin/makeup/<uuid:makeup_id>/extend/', views.ExtendDeadlineView.as_view(), name='extend_deadline'),
    path('admin/makeup/<uuid:makeup_id>/extend/form/', views.ExtendDeadlineFormView.as_view(), name='extend_deadline_form'),
    path('admin/makeup/statistics/', views.MakeupStatisticsView.as_view(), name='makeup_statistics'),
]
```

---

## COMPLETION CHECKLIST

- [ ] 30-day countdown system working
- [ ] Progress bars visual and accurate
- [ ] Urgent warnings at 7 days
- [ ] Rescheduling interface functional
- [ ] Available slots finder accurate
- [ ] Group lesson capacity respected
- [ ] Auto-expiration cron running
- [ ] Expiration warnings sent daily
- [ ] Admin extension feature working
- [ ] Statistics dashboard complete
- [ ] Notifications sent correctly
- [ ] HTMX interactions smooth

---

**Next Phase**: Phase 7 - Invoicing System
