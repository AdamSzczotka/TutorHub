# Phase 6 - Sprint 6.1: Cancellation System (Django)

## Tasks 077-081: Cancellation Requests & Admin Approval

> **Duration**: Week 10 (First half of Phase 6)
> **Goal**: Complete cancellation request system with admin approval workflow
> **Dependencies**: Phase 5 completed (Attendance system)

---

## SPRINT OVERVIEW

| Task ID | Description                          | Priority | Dependencies     |
| ------- | ------------------------------------ | -------- | ---------------- |
| 077     | Cancellation request model & UI      | Critical | Phase 5 complete |
| 078     | Admin approval workflow              | Critical | Task 077         |
| 079     | CancellationService (24h validation) | Critical | Task 078         |
| 080     | Notifications system                 | High     | Task 079         |
| 081     | Invoice corrections                  | High     | Task 080         |

---

## CANCELLATION MODELS

**File**: `apps/cancellations/models.py`

```python
from django.db import models
from django.conf import settings
import uuid


class CancellationRequest(models.Model):
    """Model for lesson cancellation requests."""

    STATUS_CHOICES = [
        ('PENDING', 'Oczekująca'),
        ('APPROVED', 'Zaakceptowana'),
        ('REJECTED', 'Odrzucona'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lesson = models.ForeignKey(
        'lessons.Lesson',
        on_delete=models.CASCADE,
        related_name='cancellation_requests'
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cancellation_requests'
    )
    reason = models.TextField('Powód')
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='PENDING')

    request_date = models.DateTimeField('Data zgłoszenia', auto_now_add=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_cancellations'
    )
    reviewed_at = models.DateTimeField('Data rozpatrzenia', null=True, blank=True)
    admin_notes = models.TextField('Notatka administratora', blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cancellation_requests'
        verbose_name = 'Prośba o anulowanie'
        verbose_name_plural = 'Prośby o anulowanie'
        ordering = ['-request_date']

    def __str__(self):
        return f"Anulowanie: {self.lesson.title} - {self.student.get_full_name()}"


class MakeupLesson(models.Model):
    """Model for makeup lessons (after cancellation approval)."""

    STATUS_CHOICES = [
        ('PENDING', 'Oczekująca'),
        ('SCHEDULED', 'Zaplanowana'),
        ('COMPLETED', 'Ukończona'),
        ('EXPIRED', 'Wygasła'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='makeup_lessons'
    )
    original_lesson = models.ForeignKey(
        'lessons.Lesson',
        on_delete=models.CASCADE,
        related_name='makeup_original'
    )
    new_lesson = models.ForeignKey(
        'lessons.Lesson',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='makeup_new'
    )
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='PENDING')
    expires_at = models.DateTimeField('Data wygaśnięcia')
    notes = models.TextField('Notatki', blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'makeup_lessons'
        verbose_name = 'Zajęcia zastępcze'
        verbose_name_plural = 'Zajęcia zastępcze'
        ordering = ['expires_at']

    def __str__(self):
        return f"Odrobienie: {self.original_lesson.title} - {self.student.get_full_name()}"

    @property
    def days_remaining(self):
        """Calculate days remaining until expiration."""
        from django.utils import timezone
        from datetime import timedelta

        if self.expires_at < timezone.now():
            return 0

        delta = self.expires_at - timezone.now()
        return delta.days
```

---

## CANCELLATION SERVICE

**File**: `apps/cancellations/services.py`

```python
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
from datetime import timedelta
from .models import CancellationRequest, MakeupLesson


class CancellationService:
    """Service for handling lesson cancellations."""

    CANCELLATION_HOURS_BEFORE = 24
    MAKEUP_EXPIRY_DAYS = 30
    MONTHLY_LIMIT = 2

    def validate_24h_rule(self, lesson):
        """Check if lesson can be cancelled (24h rule)."""
        hours_until = (lesson.start_time - timezone.now()).total_seconds() / 3600

        return {
            'valid': hours_until >= self.CANCELLATION_HOURS_BEFORE,
            'hours_until': int(hours_until)
        }

    def check_monthly_limit(self, student, month=None):
        """Check monthly cancellation limit (max 2 per month)."""
        if month is None:
            month = timezone.now()

        start_of_month = month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if month.month == 12:
            end_of_month = month.replace(year=month.year + 1, month=1, day=1)
        else:
            end_of_month = month.replace(month=month.month + 1, day=1)

        approved_count = CancellationRequest.objects.filter(
            student=student,
            status='APPROVED',
            reviewed_at__gte=start_of_month,
            reviewed_at__lt=end_of_month
        ).count()

        return {
            'allowed': approved_count < self.MONTHLY_LIMIT,
            'count': approved_count,
            'limit': self.MONTHLY_LIMIT
        }

    def create_request(self, lesson, student, reason):
        """Create a cancellation request."""
        # Validate 24h rule
        validation = self.validate_24h_rule(lesson)
        if not validation['valid']:
            raise ValidationError(
                f"Nie można anulować zajęć krócej niż 24h przed rozpoczęciem. "
                f"Pozostało {validation['hours_until']}h."
            )

        # Check if student is enrolled
        if not lesson.students.filter(id=student.id).exists():
            raise ValidationError("Nie jesteś zapisany na te zajęcia.")

        # Check for existing pending request
        existing = CancellationRequest.objects.filter(
            lesson=lesson,
            student=student,
            status='PENDING'
        ).exists()

        if existing:
            raise ValidationError("Prośba o anulowanie tych zajęć już istnieje.")

        # Create request
        request = CancellationRequest.objects.create(
            lesson=lesson,
            student=student,
            reason=reason
        )

        # Send notification to admins
        self._notify_admins_new_request(request)

        return request

    @transaction.atomic
    def approve_request(self, request, admin, notes=''):
        """Approve a cancellation request."""
        if request.status != 'PENDING':
            raise ValidationError("Prośba została już rozpatrzona.")

        # Update request
        request.status = 'APPROVED'
        request.reviewed_by = admin
        request.reviewed_at = timezone.now()
        request.admin_notes = notes
        request.save()

        # Update lesson status
        request.lesson.status = 'CANCELLED'
        request.lesson.save()

        # Create makeup lesson with 30-day expiry
        expires_at = timezone.now() + timedelta(days=self.MAKEUP_EXPIRY_DAYS)

        makeup = MakeupLesson.objects.create(
            student=request.student,
            original_lesson=request.lesson,
            expires_at=expires_at,
            notes=f"Anulowano: {request.reason}"
        )

        # Send notifications
        self._notify_student_approved(request, makeup)

        return request, makeup

    @transaction.atomic
    def reject_request(self, request, admin, reason):
        """Reject a cancellation request."""
        if request.status != 'PENDING':
            raise ValidationError("Prośba została już rozpatrzona.")

        if not reason:
            raise ValidationError("Powód odrzucenia jest wymagany.")

        request.status = 'REJECTED'
        request.reviewed_by = admin
        request.reviewed_at = timezone.now()
        request.admin_notes = reason
        request.save()

        # Send notification
        self._notify_student_rejected(request)

        return request

    def get_student_stats(self, student):
        """Get cancellation statistics for a student."""
        total = CancellationRequest.objects.filter(student=student).count()
        approved = CancellationRequest.objects.filter(student=student, status='APPROVED').count()
        rejected = CancellationRequest.objects.filter(student=student, status='REJECTED').count()
        pending = CancellationRequest.objects.filter(student=student, status='PENDING').count()

        monthly = self.check_monthly_limit(student)

        return {
            'total': total,
            'approved': approved,
            'rejected': rejected,
            'pending': pending,
            'monthly_used': monthly['count'],
            'monthly_limit': monthly['limit'],
            'monthly_remaining': monthly['limit'] - monthly['count']
        }

    def _notify_admins_new_request(self, request):
        """Notify admins about new cancellation request."""
        from apps.notifications.services import notification_service
        from apps.accounts.models import User

        admins = User.objects.filter(role='ADMIN', is_active=True)

        for admin in admins:
            notification_service.create(
                user=admin,
                notification_type='NEW_CANCELLATION_REQUEST',
                title='Nowa prośba o anulowanie',
                message=f'{request.student.get_full_name()} prosi o anulowanie zajęć "{request.lesson.title}"'
            )

    def _notify_student_approved(self, request, makeup):
        """Notify student about approved cancellation."""
        from apps.notifications.services import notification_service

        notification_service.create(
            user=request.student,
            notification_type='CANCELLATION_APPROVED',
            title='Anulowanie zaakceptowane',
            message=f'Twoja prośba o anulowanie zajęć "{request.lesson.title}" została zaakceptowana. '
                    f'Masz 30 dni na umówienie zajęć zastępczych.'
        )

    def _notify_student_rejected(self, request):
        """Notify student about rejected cancellation."""
        from apps.notifications.services import notification_service

        notification_service.create(
            user=request.student,
            notification_type='CANCELLATION_REJECTED',
            title='Anulowanie odrzucone',
            message=f'Twoja prośba o anulowanie zajęć "{request.lesson.title}" została odrzucona. '
                    f'Powód: {request.admin_notes}'
        )


cancellation_service = CancellationService()
```

---

## CANCELLATION VIEWS

**File**: `apps/cancellations/views.py`

```python
from django.views.generic import ListView, View, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone

from apps.core.mixins import AdminRequiredMixin, HTMXMixin
from apps.lessons.models import Lesson
from .models import CancellationRequest
from .services import cancellation_service


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
                reason=reason
            )

            return HttpResponse(
                '''<div class="alert alert-success">
                    Prośba o anulowanie została wysłana. Administrator otrzyma powiadomienie.
                </div>''',
                headers={'HX-Trigger': 'cancellationCreated'}
            )

        except Exception as e:
            return HttpResponse(
                f'<div class="alert alert-error">{str(e)}</div>',
                status=400
            )


class StudentCancellationsView(LoginRequiredMixin, HTMXMixin, ListView):
    """Display student's cancellation requests."""
    template_name = 'cancellations/student_list.html'
    partial_template_name = 'cancellations/partials/_student_list.html'
    context_object_name = 'requests'

    def get_queryset(self):
        return CancellationRequest.objects.filter(
            student=self.request.user
        ).select_related(
            'lesson', 'lesson__subject', 'lesson__tutor'
        ).order_by('-request_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stats'] = cancellation_service.get_student_stats(self.request.user)
        return context


# Admin Views
class AdminCancellationQueueView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, ListView):
    """Admin view for pending cancellation requests."""
    template_name = 'admin_panel/cancellations/queue.html'
    partial_template_name = 'admin_panel/cancellations/partials/_queue_list.html'
    context_object_name = 'requests'

    def get_queryset(self):
        status = self.request.GET.get('status', 'PENDING')
        return CancellationRequest.objects.filter(
            status=status
        ).select_related(
            'lesson', 'lesson__subject', 'lesson__tutor',
            'student', 'student__student_profile'
        ).order_by('-request_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_status'] = self.request.GET.get('status', 'PENDING')
        context['pending_count'] = CancellationRequest.objects.filter(status='PENDING').count()
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
                    notes=notes
                )
                message = 'Prośba została zaakceptowana.'
            elif action == 'REJECT':
                if not notes:
                    return HttpResponse(
                        '<div class="alert alert-error">Podaj powód odrzucenia.</div>',
                        status=400
                    )
                cancellation_service.reject_request(
                    cancellation_request,
                    admin=request.user,
                    reason=notes
                )
                message = 'Prośba została odrzucona.'
            else:
                return HttpResponse(
                    '<div class="alert alert-error">Nieprawidłowa akcja.</div>',
                    status=400
                )

            return HttpResponse(
                f'<div class="alert alert-success">{message}</div>',
                headers={'HX-Trigger': 'cancellationReviewed'}
            )

        except Exception as e:
            return HttpResponse(
                f'<div class="alert alert-error">{str(e)}</div>',
                status=400
            )


class ReviewFormView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    """Display review form for a cancellation request."""
    template_name = 'admin_panel/cancellations/partials/_review_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request_id = self.kwargs.get('request_id')
        context['cancellation'] = get_object_or_404(CancellationRequest, id=request_id)
        return context
```

---

## CANCELLATION TEMPLATES

**File**: `templates/cancellations/request_form.html`

```html
{% extends "base.html" %}

{% block content %}
<div class="max-w-md mx-auto">
    {% include "cancellations/partials/_request_form.html" %}
</div>
{% endblock %}
```

**File**: `templates/cancellations/partials/_request_form.html`

```html
<div class="card bg-base-100 shadow-xl">
    <div class="card-body">
        <h2 class="card-title">Anulowanie zajęć</h2>

        <!-- Lesson Details -->
        <div class="bg-base-200 rounded-lg p-4 space-y-2">
            <div class="flex items-center gap-2 text-sm">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                          d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/>
                </svg>
                <span class="font-medium">{{ lesson.title }}</span>
            </div>
            <div class="text-sm text-base-content/70">
                {{ lesson.start_time|date:"l, d F Y, H:i" }}
            </div>
            {% if lesson.subject %}
            <div class="text-sm text-base-content/70">
                Przedmiot: {{ lesson.subject.name }}
            </div>
            {% endif %}
            {% if lesson.tutor %}
            <div class="text-sm text-base-content/70">
                Korepetytor: {{ lesson.tutor.get_full_name }}
            </div>
            {% endif %}
        </div>

        {% if not can_cancel %}
        <!-- 24h Warning -->
        <div class="alert alert-error">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                      d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
            </svg>
            <div>
                <h3 class="font-bold">Nie można anulować</h3>
                <p class="text-sm">
                    Nie można anulować zajęć krócej niż 24 godziny przed rozpoczęciem.
                    Pozostało tylko {{ hours_until }}h. Skontaktuj się z administratorem.
                </p>
            </div>
        </div>

        <div class="card-actions justify-end">
            <button class="btn btn-outline" onclick="history.back()">Zamknij</button>
        </div>

        {% else %}
        <!-- Can Cancel -->
        <div class="alert alert-info">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                      d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
            <div>
                <p class="text-sm">
                    Zajęcia rozpoczną się za {{ hours_until }} godzin. Po akceptacji przez
                    administratora zajęcia trafią do systemu odrabiania (30 dni na umówienie).
                </p>
            </div>
        </div>

        <form hx-post="{% url 'cancellations:create' lesson.id %}"
              hx-target="#form-result"
              hx-swap="innerHTML"
              class="space-y-4">
            {% csrf_token %}

            <div id="form-result"></div>

            <div class="form-control">
                <label class="label">
                    <span class="label-text">Powód anulowania *</span>
                </label>
                <textarea name="reason"
                          class="textarea textarea-bordered w-full"
                          rows="4"
                          placeholder="Opisz powód anulowania zajęć (min. 10 znaków)..."
                          minlength="10"
                          required></textarea>
                <label class="label">
                    <span class="label-text-alt">
                        Podaj szczegółowy powód - pomoże to administratorowi podjąć decyzję
                    </span>
                </label>
            </div>

            <div class="card-actions justify-end">
                <button type="button" class="btn btn-outline" onclick="history.back()">
                    Anuluj
                </button>
                <button type="submit" class="btn btn-primary">
                    Wyślij prośbę
                </button>
            </div>
        </form>
        {% endif %}
    </div>
</div>
```

---

## ADMIN QUEUE TEMPLATES

**File**: `templates/admin_panel/cancellations/queue.html`

```html
{% extends "admin_panel/base.html" %}

{% block content %}
<div class="space-y-6">
    <div class="flex items-center justify-between">
        <div>
            <h1 class="text-2xl font-bold">Prośby o anulowanie zajęć</h1>
            <p class="text-base-content/70">Zarządzaj prośbami o anulowanie zajęć od uczniów</p>
        </div>

        {% if pending_count > 0 %}
        <span class="badge badge-warning badge-lg">
            {{ pending_count }} oczekujących
        </span>
        {% endif %}
    </div>

    <!-- Tabs -->
    <div class="tabs tabs-boxed">
        <a class="tab {% if current_status == 'PENDING' %}tab-active{% endif %}"
           hx-get="{% url 'cancellations:admin_queue' %}?status=PENDING"
           hx-target="#requests-list"
           hx-swap="innerHTML"
           hx-push-url="true">
            Oczekujące
        </a>
        <a class="tab {% if current_status == 'APPROVED' %}tab-active{% endif %}"
           hx-get="{% url 'cancellations:admin_queue' %}?status=APPROVED"
           hx-target="#requests-list"
           hx-swap="innerHTML"
           hx-push-url="true">
            Zaakceptowane
        </a>
        <a class="tab {% if current_status == 'REJECTED' %}tab-active{% endif %}"
           hx-get="{% url 'cancellations:admin_queue' %}?status=REJECTED"
           hx-target="#requests-list"
           hx-swap="innerHTML"
           hx-push-url="true">
            Odrzucone
        </a>
    </div>

    <div id="requests-list"
         hx-get="{% url 'cancellations:admin_queue' %}?status={{ current_status }}"
         hx-trigger="cancellationReviewed from:body"
         hx-swap="innerHTML">
        {% include "admin_panel/cancellations/partials/_queue_list.html" %}
    </div>
</div>

<!-- Review Modal -->
<dialog id="review-modal" class="modal">
    <div class="modal-box max-w-lg">
        <div id="review-modal-content"></div>
    </div>
    <form method="dialog" class="modal-backdrop">
        <button>close</button>
    </form>
</dialog>
{% endblock %}
```

**File**: `templates/admin_panel/cancellations/partials/_queue_list.html`

```html
{% if requests %}
<div class="space-y-4">
    {% for req in requests %}
    <div class="card bg-base-100 shadow">
        <div class="card-body">
            <div class="flex items-start justify-between">
                <div class="space-y-1">
                    <h3 class="card-title text-lg">{{ req.lesson.title }}</h3>
                    <div class="flex items-center gap-4 text-sm text-base-content/70">
                        <div class="flex items-center gap-1">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                      d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/>
                            </svg>
                            {{ req.lesson.start_time|date:"d.m.Y, H:i" }}
                        </div>
                        <div class="flex items-center gap-1">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                      d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
                            </svg>
                            {{ req.student.get_full_name }}
                        </div>
                    </div>
                </div>

                {% if req.status == 'PENDING' %}
                <span class="badge badge-warning gap-1">
                    <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                              d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                    </svg>
                    Oczekuje
                </span>
                {% elif req.status == 'APPROVED' %}
                <span class="badge badge-success gap-1">
                    <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                              d="M5 13l4 4L19 7"/>
                    </svg>
                    Zaakceptowana
                </span>
                {% else %}
                <span class="badge badge-error gap-1">
                    <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                              d="M6 18L18 6M6 6l12 12"/>
                    </svg>
                    Odrzucona
                </span>
                {% endif %}
            </div>

            <!-- Reason -->
            <div class="mt-4">
                <div class="flex items-center gap-2 mb-2">
                    <svg class="w-4 h-4 text-base-content/50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                    </svg>
                    <span class="font-medium text-sm">Powód:</span>
                </div>
                <p class="text-sm text-base-content/80 bg-base-200 p-3 rounded-lg">
                    {{ req.reason }}
                </p>
            </div>

            <div class="flex items-center justify-between pt-4 border-t mt-4">
                <div class="text-xs text-base-content/50">
                    Wysłano: {{ req.request_date|date:"d.m.Y, H:i" }}
                </div>

                {% if req.status == 'PENDING' %}
                <button class="btn btn-sm btn-primary"
                        hx-get="{% url 'cancellations:review_form' req.id %}"
                        hx-target="#review-modal-content"
                        onclick="document.getElementById('review-modal').showModal()">
                    Rozpatrz
                </button>
                {% elif req.admin_notes %}
                <div class="text-xs">
                    <span class="font-medium">Notatka admina:</span>
                    {{ req.admin_notes|truncatewords:15 }}
                </div>
                {% endif %}
            </div>
        </div>
    </div>
    {% endfor %}
</div>
{% else %}
<div class="card bg-base-100 shadow">
    <div class="card-body py-12 text-center text-base-content/50">
        Brak próśb o anulowanie
    </div>
</div>
{% endif %}
```

**File**: `templates/admin_panel/cancellations/partials/_review_form.html`

```html
<h3 class="font-bold text-lg mb-4">Rozpatrz prośbę o anulowanie</h3>

<!-- Lesson Details -->
<div class="bg-info/10 border border-info/30 rounded-lg p-4 space-y-2 mb-4">
    <h4 class="font-semibold text-info-content">{{ cancellation.lesson.title }}</h4>
    <div class="text-sm text-info-content/80">
        Data: {{ cancellation.lesson.start_time|date:"d.m.Y, H:i" }}
    </div>
    <div class="text-sm text-info-content/80">
        Uczeń: {{ cancellation.student.get_full_name }}
    </div>
</div>

<!-- Student's Reason -->
<div class="mb-4">
    <div class="font-medium text-sm mb-2">Powód ucznia:</div>
    <div class="bg-base-200 p-3 rounded-lg text-sm">
        {{ cancellation.reason }}
    </div>
</div>

<!-- Info Alert -->
<div class="alert alert-info mb-4">
    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
    </svg>
    <span class="text-sm">
        Po zaakceptowaniu zajęcia zostaną anulowane, a uczeń otrzyma prawo do
        odrobienia zajęć w ciągu 30 dni.
    </span>
</div>

<form hx-post="{% url 'cancellations:review' cancellation.id %}"
      hx-target="#requests-list"
      hx-swap="innerHTML"
      x-data="{ action: '' }"
      class="space-y-4">
    {% csrf_token %}

    <input type="hidden" name="action" x-model="action">

    <div class="form-control">
        <label class="label">
            <span class="label-text">Notatka administratora (opcjonalna dla akceptacji, wymagana dla odrzucenia)</span>
        </label>
        <textarea name="notes"
                  class="textarea textarea-bordered w-full"
                  rows="3"
                  placeholder="Dodatkowe informacje lub komentarz..."></textarea>
    </div>

    <div class="flex items-center justify-end gap-2 pt-4 border-t">
        <button type="button"
                class="btn btn-ghost"
                onclick="document.getElementById('review-modal').close()">
            Anuluj
        </button>
        <button type="submit"
                class="btn btn-error gap-2"
                @click="action = 'REJECT'">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                      d="M6 18L18 6M6 6l12 12"/>
            </svg>
            Odrzuć
        </button>
        <button type="submit"
                class="btn btn-success gap-2"
                @click="action = 'APPROVE'">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                      d="M5 13l4 4L19 7"/>
            </svg>
            Zaakceptuj
        </button>
    </div>
</form>
```

---

## INVOICE CORRECTION SERVICE

**File**: `apps/invoices/services.py` (rozszerzenie)

```python
from django.db import transaction
from decimal import Decimal


class InvoiceCorrectionService:
    """Service for invoice corrections after cancellations."""

    @transaction.atomic
    def correct_for_cancellation(self, lesson, student):
        """Remove cancelled lesson from invoice."""
        from .models import InvoiceItem, Invoice

        # Find invoice item for this lesson
        invoice_item = InvoiceItem.objects.filter(
            lesson=lesson,
            invoice__student=student,
            invoice__status__in=['GENERATED', 'SENT']
        ).select_related('invoice').first()

        if not invoice_item:
            return None  # Not billed yet

        invoice = invoice_item.invoice

        # Remove item
        item_amount = invoice_item.total_price
        invoice_item.delete()

        # Recalculate invoice totals
        remaining_items = InvoiceItem.objects.filter(invoice=invoice)

        net_amount = sum(item.total_price for item in remaining_items)
        vat_amount = net_amount * Decimal('0.23')
        total_amount = net_amount + vat_amount

        invoice.net_amount = net_amount
        invoice.vat_amount = vat_amount
        invoice.total_amount = total_amount
        invoice.status = 'CORRECTED'
        invoice.notes = f"{invoice.notes or ''}\nKorekta - anulowanie zajęć (Lesson ID: {lesson.id})"
        invoice.save()

        return {
            'invoice_id': invoice.id,
            'corrected_amount': item_amount,
            'new_total': total_amount
        }

    @transaction.atomic
    def create_credit_note(self, original_invoice, lesson, amount):
        """Create credit note for already paid invoice."""
        from .models import Invoice
        from django.utils import timezone

        now = timezone.now()
        year = now.year
        month = str(now.month).zfill(2)

        # Generate credit note number
        last_credit = Invoice.objects.filter(
            invoice_number__startswith=f'KOR/{year}/{month}/'
        ).order_by('-invoice_number').first()

        if last_credit:
            last_num = int(last_credit.invoice_number.split('/')[-1])
            sequence = last_num + 1
        else:
            sequence = 1

        credit_number = f"KOR/{year}/{month}/{str(sequence).zfill(3)}"

        # Create credit note (negative amounts)
        credit_note = Invoice.objects.create(
            invoice_number=credit_number,
            student=original_invoice.student,
            month_year=original_invoice.month_year,
            net_amount=-amount,
            vat_amount=-(amount * Decimal('0.23')),
            total_amount=-(amount * Decimal('1.23')),
            status='GENERATED',
            issue_date=now.date(),
            due_date=now.date(),
            notes=f"Korekta faktury {original_invoice.invoice_number} - anulowanie zajęć"
        )

        return credit_note


invoice_correction_service = InvoiceCorrectionService()
```

---

## CELERY TASKS

**File**: `apps/cancellations/tasks.py`

```python
from celery import shared_task


@shared_task
def send_cancellation_notification_email(request_id, notification_type):
    """Send email notification for cancellation."""
    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    from django.conf import settings
    from .models import CancellationRequest

    request = CancellationRequest.objects.select_related(
        'student', 'lesson', 'lesson__subject'
    ).get(id=request_id)

    if notification_type == 'approved':
        template = 'emails/cancellation_approved.html'
        subject = f"Anulowanie zaakceptowane - {request.lesson.title}"
    else:
        template = 'emails/cancellation_rejected.html'
        subject = f"Anulowanie odrzucone - {request.lesson.title}"

    context = {
        'student_name': request.student.get_full_name(),
        'lesson_title': request.lesson.title,
        'lesson_date': request.lesson.start_time,
        'admin_notes': request.admin_notes,
    }

    html_content = render_to_string(template, context)

    send_mail(
        subject=subject,
        message='',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[request.student.email],
        html_message=html_content
    )


@shared_task
def notify_admin_new_cancellation(request_id):
    """Notify admins about new cancellation request."""
    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    from django.conf import settings
    from apps.accounts.models import User
    from .models import CancellationRequest

    request = CancellationRequest.objects.select_related(
        'student', 'lesson', 'lesson__subject'
    ).get(id=request_id)

    admins = User.objects.filter(role='ADMIN', is_active=True)

    context = {
        'student_name': request.student.get_full_name(),
        'lesson_title': request.lesson.title,
        'lesson_date': request.lesson.start_time,
        'reason': request.reason,
    }

    html_content = render_to_string('emails/new_cancellation_request.html', context)

    for admin in admins:
        send_mail(
            subject=f"Nowa prośba o anulowanie - {request.lesson.title}",
            message='',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[admin.email],
            html_message=html_content
        )
```

---

## URL CONFIGURATION

**File**: `apps/cancellations/urls.py`

```python
from django.urls import path
from . import views

app_name = 'cancellations'

urlpatterns = [
    # Student views
    path('request/<uuid:lesson_id>/', views.CancellationRequestFormView.as_view(), name='request_form'),
    path('request/<uuid:lesson_id>/create/', views.CreateCancellationRequestView.as_view(), name='create'),
    path('my-requests/', views.StudentCancellationsView.as_view(), name='my_requests'),

    # Admin views
    path('admin/queue/', views.AdminCancellationQueueView.as_view(), name='admin_queue'),
    path('admin/review/<uuid:request_id>/', views.ReviewCancellationView.as_view(), name='review'),
    path('admin/review/<uuid:request_id>/form/', views.ReviewFormView.as_view(), name='review_form'),
]
```

---

## COMPLETION CHECKLIST

- [ ] CancellationRequest model created
- [ ] MakeupLesson model created
- [ ] 24h validation working (client + server)
- [ ] Monthly limit (2 cancellations) enforced
- [ ] Admin approval workflow functional
- [ ] CancellationService complete
- [ ] Notifications sent on approve/reject
- [ ] Invoice corrections working
- [ ] Email notifications sent
- [ ] HTMX interactions smooth

---

**Next Sprint**: 6.2 - Makeup Lessons System
