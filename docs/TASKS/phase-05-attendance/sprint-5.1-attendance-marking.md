# Phase 5 - Sprint 5.1: Attendance Marking (Django)

## Tasks 067-071: Attendance Registration System

> **Duration**: Week 9 (First half of Phase 5)
> **Goal**: Complete attendance marking system with multiple status support and time tracking
> **Dependencies**: Phase 4 completed (Calendar & Lesson Management)

---

## SPRINT OVERVIEW

| Task ID | Description                        | Priority | Dependencies     |
| ------- | ---------------------------------- | -------- | ---------------- |
| 067     | Attendance marking UI (HTMX)       | Critical | Phase 4 complete |
| 068     | AttendanceService implementation   | Critical | Task 067         |
| 069     | Attendance statuses system         | Critical | Task 068         |
| 070     | Time tracking (check-in/check-out) | High     | Task 069         |
| 071     | Group attendance management        | High     | Task 070         |

---

## ATTENDANCE MODELS

**File**: `apps/attendance/models.py`

```python
from django.db import models
from django.utils import timezone
from apps.core.models import BaseModel


class AttendanceStatus(models.TextChoices):
    PRESENT = 'PRESENT', 'Obecny'
    ABSENT = 'ABSENT', 'Nieobecny'
    LATE = 'LATE', 'Spóźniony'
    EXCUSED = 'EXCUSED', 'Usprawiedliwiony'
    PENDING = 'PENDING', 'Oczekujące'


class AttendanceAlert(BaseModel):
    """Model for low attendance alerts."""

    class AlertStatus(models.TextChoices):
        PENDING = 'PENDING', 'Oczekujący'
        RESOLVED = 'RESOLVED', 'Rozwiązany'
        DISMISSED = 'DISMISSED', 'Odrzucony'

    student = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='attendance_alerts'
    )
    attendance_rate = models.DecimalField(max_digits=5, decimal_places=2)
    threshold = models.PositiveIntegerField(default=80)
    alert_type = models.CharField(max_length=50, default='LOW_ATTENDANCE')
    status = models.CharField(
        max_length=20,
        choices=AlertStatus.choices,
        default=AlertStatus.PENDING
    )
    resolution = models.TextField(blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'attendance_alerts'
        ordering = ['-created_at']


class AttendanceReport(BaseModel):
    """Model for monthly attendance reports."""

    student = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='attendance_reports'
    )
    month = models.DateField()
    attendance_rate = models.DecimalField(max_digits=5, decimal_places=2)
    total_lessons = models.PositiveIntegerField()
    present_count = models.PositiveIntegerField()
    absent_count = models.PositiveIntegerField()
    late_count = models.PositiveIntegerField()
    excused_count = models.PositiveIntegerField()
    pdf_path = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'attendance_reports'
        unique_together = ['student', 'month']
        ordering = ['-month']
```

---

## ATTENDANCE SERVICE

**File**: `apps/attendance/services.py`

```python
from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from apps.lessons.models import LessonStudent, Lesson
from apps.accounts.models import User
from .models import AttendanceStatus, AttendanceAlert


class AttendanceService:
    """Service for attendance operations."""

    def mark_attendance(
        self,
        lesson_id: str,
        student_id: str,
        status: str,
        notes: Optional[str] = None,
        check_in_time: Optional[datetime] = None,
        check_out_time: Optional[datetime] = None
    ) -> LessonStudent:
        """Mark attendance for a single student."""

        lesson_student = LessonStudent.objects.select_related(
            'lesson', 'student'
        ).get(
            lesson_id=lesson_id,
            student_id=student_id
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
        attendance_records: List[Dict[str, Any]]
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
                student_id=student_id
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
        end_date: datetime
    ) -> List[LessonStudent]:
        """Get attendance history for a student."""

        return LessonStudent.objects.filter(
            student_id=student_id,
            lesson__start_time__gte=start_date,
            lesson__start_time__lte=end_date,
            lesson__deleted_at__isnull=True
        ).select_related(
            'lesson__subject',
            'lesson__level',
            'lesson__tutor',
            'lesson__room'
        ).order_by('-lesson__start_time')

    def calculate_statistics(
        self,
        student_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Calculate attendance statistics for a student."""

        queryset = LessonStudent.objects.filter(
            student_id=student_id,
            lesson__deleted_at__isnull=True,
            lesson__status__in=['SCHEDULED', 'ONGOING', 'COMPLETED']
        )

        if start_date:
            queryset = queryset.filter(lesson__start_time__gte=start_date)
        if end_date:
            queryset = queryset.filter(lesson__start_time__lte=end_date)

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
        threshold: int = 80
    ) -> List[Dict[str, Any]]:
        """Get students with attendance below threshold."""

        students = User.objects.filter(
            role='STUDENT',
            is_active=True,
            deleted_at__isnull=True
        )

        students_at_risk = []

        for student in students:
            stats = self.calculate_statistics(student.id)
            if stats['total'] > 0 and stats['attendance_rate'] < threshold:
                students_at_risk.append({
                    'student': student,
                    'stats': stats,
                })

        return students_at_risk

    def check_in(self, lesson_id: str, student_id: str) -> LessonStudent:
        """Record check-in time."""

        lesson_student = LessonStudent.objects.get(
            lesson_id=lesson_id,
            student_id=student_id
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

            lesson_student.save()

        return lesson_student

    def check_out(self, lesson_id: str, student_id: str) -> LessonStudent:
        """Record check-out time."""

        lesson_student = LessonStudent.objects.get(
            lesson_id=lesson_id,
            student_id=student_id
        )

        if lesson_student.check_in_time and not lesson_student.check_out_time:
            lesson_student.check_out_time = timezone.now()
            lesson_student.save()

        return lesson_student

    def _update_lesson_status(self, lesson_id: str):
        """Update lesson status based on attendance."""

        lesson = Lesson.objects.prefetch_related('lesson_students').get(pk=lesson_id)
        now = timezone.now()

        # Check if lesson has ended
        if lesson.end_time < now:
            all_marked = all(
                ls.attendance_status != AttendanceStatus.PENDING
                for ls in lesson.lesson_students.all()
            )

            if all_marked and lesson.status != 'COMPLETED':
                lesson.status = 'COMPLETED'
                lesson.save()

        elif lesson.start_time <= now < lesson.end_time:
            if lesson.status == 'SCHEDULED':
                lesson.status = 'ONGOING'
                lesson.save()


attendance_service = AttendanceService()
```

---

## ATTENDANCE VIEWS

**File**: `apps/attendance/views.py`

```python
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
import json

from apps.core.mixins import TutorRequiredMixin, HTMXMixin
from apps.lessons.models import Lesson, LessonStudent
from .services import attendance_service
from .models import AttendanceStatus


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
            pk=lesson_id
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
                notes=notes
            )

            return JsonResponse({
                'success': True,
                'status': lesson_student.attendance_status,
                'marked_at': lesson_student.attendance_marked_at.isoformat()
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
            count = attendance_service.bulk_mark_attendance(
                lesson_id=str(lesson_id),
                attendance_records=records
            )

            return HttpResponse(
                status=204,
                headers={
                    'HX-Trigger': 'attendanceSaved',
                    'HX-Reswap': 'none',
                }
            )

        return HttpResponse('Brak zmian do zapisania', status=400)


class CheckInView(LoginRequiredMixin, View):
    """Check-in endpoint."""

    def post(self, request, lesson_id, student_id):
        try:
            lesson_student = attendance_service.check_in(
                lesson_id=str(lesson_id),
                student_id=str(student_id)
            )

            if request.htmx:
                return HttpResponse(
                    f'<span class="badge badge-success">{lesson_student.check_in_time.strftime("%H:%M:%S")}</span>'
                )

            return JsonResponse({
                'success': True,
                'check_in_time': lesson_student.check_in_time.isoformat()
            })

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


class CheckOutView(LoginRequiredMixin, View):
    """Check-out endpoint."""

    def post(self, request, lesson_id, student_id):
        try:
            lesson_student = attendance_service.check_out(
                lesson_id=str(lesson_id),
                student_id=str(student_id)
            )

            if request.htmx:
                return HttpResponse(
                    f'<span class="badge badge-success">{lesson_student.check_out_time.strftime("%H:%M:%S")}</span>'
                )

            return JsonResponse({
                'success': True,
                'check_out_time': lesson_student.check_out_time.isoformat()
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
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')

        if not start_date:
            start_date = timezone.now() - timezone.timedelta(days=30)
        else:
            start_date = timezone.datetime.fromisoformat(start_date)

        if not end_date:
            end_date = timezone.now()
        else:
            end_date = timezone.datetime.fromisoformat(end_date)

        context['history'] = attendance_service.get_attendance_history(
            student_id=str(student_id),
            start_date=start_date,
            end_date=end_date
        )
        context['statistics'] = attendance_service.calculate_statistics(
            student_id=str(student_id),
            start_date=start_date,
            end_date=end_date
        )
        context['start_date'] = start_date
        context['end_date'] = end_date

        return context
```

---

## ATTENDANCE TEMPLATES

### Main Attendance Marking Template

**File**: `templates/attendance/marking.html`

```html
{% extends "tutor_panel/base.html" %}

{% block content %}
<div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
        <div>
            <h1 class="text-2xl font-bold flex items-center gap-2">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/>
                </svg>
                Lista obecności
            </h1>
            <p class="text-base-content/60 mt-1">
                {{ lesson.title }} &bull; {{ lesson.start_time|date:"j E Y" }} &bull; {{ lesson.start_time|time:"H:i" }}
            </p>
        </div>

        <div class="flex gap-2">
            <div class="badge badge-secondary">
                <span id="marked-count">0</span> / {{ students|length }} oznaczonych
            </div>
        </div>
    </div>

    <!-- Attendance Form -->
    <form hx-post="{% url 'attendance:bulk_mark' lesson.pk %}"
          hx-swap="none"
          id="attendance-form">
        {% csrf_token %}

        <!-- Bulk Actions -->
        <div class="flex items-center gap-2 p-4 bg-base-200 rounded-lg mb-4">
            <button type="button"
                    onclick="markAllPresent()"
                    class="btn btn-sm btn-outline btn-success">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                </svg>
                Wszyscy obecni
            </button>
            <button type="button"
                    onclick="resetAll()"
                    class="btn btn-sm btn-outline">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
                </svg>
                Resetuj
            </button>
        </div>

        <!-- Student List -->
        <div class="bg-base-100 rounded-lg border divide-y">
            {% for ls in students %}
            <div class="p-4 flex items-start justify-between gap-4" id="student-row-{{ ls.student.id }}">
                <div class="flex-1">
                    <div class="flex items-center gap-2">
                        <span class="font-medium">{{ forloop.counter }}. {{ ls.student.get_full_name }}</span>
                        <span class="badge badge-outline badge-sm">
                            {{ ls.student.student_profile.class_name|default:"N/A" }}
                        </span>
                    </div>
                    <p class="text-sm text-base-content/60">{{ ls.student.email }}</p>
                </div>

                <!-- Status Buttons -->
                <div class="flex gap-2" x-data="{ status: '{{ ls.attendance_status }}' }">
                    {% for value, label in statuses %}
                    {% if value != 'PENDING' %}
                    <button type="button"
                            class="btn btn-sm"
                            :class="status === '{{ value }}' ? getButtonClass('{{ value }}') : 'btn-outline'"
                            @click="status = '{{ value }}'; updateHiddenInput('{{ ls.student.id }}', '{{ value }}')">
                        {% if value == 'PRESENT' %}
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                            </svg>
                        {% elif value == 'ABSENT' %}
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                            </svg>
                        {% elif value == 'LATE' %}
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                            </svg>
                        {% else %}
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
                            </svg>
                        {% endif %}
                        <span class="hidden sm:inline">{{ label }}</span>
                    </button>
                    {% endif %}
                    {% endfor %}

                    <input type="hidden"
                           name="status_{{ ls.student.id }}"
                           id="status-{{ ls.student.id }}"
                           value="{{ ls.attendance_status }}">
                </div>
            </div>

            <!-- Notes (expanded when status is set) -->
            <div class="px-4 pb-4 ml-6"
                 x-show="status && status !== 'PENDING'"
                 x-cloak>
                <label class="label">
                    <span class="label-text text-sm">Notatki (opcjonalne)</span>
                </label>
                <textarea name="notes_{{ ls.student.id }}"
                          class="textarea textarea-bordered textarea-sm w-full"
                          rows="2"
                          placeholder="Dodatkowe informacje...">{{ ls.attendance_notes }}</textarea>
            </div>
            {% endfor %}
        </div>

        <!-- Save Button -->
        <div class="flex justify-end mt-4">
            <button type="submit" class="btn btn-primary">
                <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                </svg>
                Zapisz obecność
            </button>
        </div>
    </form>
</div>

<script>
function getButtonClass(status) {
    const classes = {
        'PRESENT': 'btn-success',
        'ABSENT': 'btn-error',
        'LATE': 'btn-warning',
        'EXCUSED': 'btn-info',
    };
    return classes[status] || 'btn-outline';
}

function updateHiddenInput(studentId, status) {
    document.getElementById(`status-${studentId}`).value = status;
    updateMarkedCount();
}

function markAllPresent() {
    document.querySelectorAll('[id^="status-"]').forEach(input => {
        input.value = 'PRESENT';
    });
    // Trigger Alpine updates
    document.querySelectorAll('[x-data]').forEach(el => {
        el.__x.$data.status = 'PRESENT';
    });
    updateMarkedCount();
}

function resetAll() {
    document.querySelectorAll('[id^="status-"]').forEach(input => {
        input.value = 'PENDING';
    });
    document.querySelectorAll('[x-data]').forEach(el => {
        el.__x.$data.status = 'PENDING';
    });
    updateMarkedCount();
}

function updateMarkedCount() {
    const inputs = document.querySelectorAll('[id^="status-"]');
    const markedCount = Array.from(inputs).filter(i => i.value !== 'PENDING').length;
    document.getElementById('marked-count').textContent = markedCount;
}

// HTMX event listeners
document.body.addEventListener('attendanceSaved', function() {
    const toast = document.createElement('div');
    toast.className = 'toast toast-end';
    toast.innerHTML = '<div class="alert alert-success"><span>Obecność została zapisana</span></div>';
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
});

// Initial count
updateMarkedCount();
</script>
{% endblock %}
```

### Time Tracking Component

**File**: `templates/attendance/partials/_time_tracker.html`

```html
<div class="card bg-base-100 shadow-sm">
    <div class="card-body p-4">
        <h3 class="card-title text-base flex items-center gap-2">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
            Śledzenie czasu
        </h3>

        <div class="grid grid-cols-2 gap-4 mt-4">
            <!-- Check-in -->
            <div>
                <div class="text-sm font-medium text-base-content/70 mb-2">Wejście</div>
                <div id="checkin-display-{{ student_id }}">
                    {% if lesson_student.check_in_time %}
                        <span class="badge badge-success">
                            {{ lesson_student.check_in_time|time:"H:i:s" }}
                        </span>
                    {% else %}
                        <button class="btn btn-sm btn-outline w-full"
                                hx-post="{% url 'attendance:check_in' lesson_id student_id %}"
                                hx-target="#checkin-display-{{ student_id }}"
                                hx-swap="innerHTML">
                            <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1"/>
                            </svg>
                            Wejście
                        </button>
                    {% endif %}
                </div>
            </div>

            <!-- Check-out -->
            <div>
                <div class="text-sm font-medium text-base-content/70 mb-2">Wyjście</div>
                <div id="checkout-display-{{ student_id }}">
                    {% if lesson_student.check_out_time %}
                        <span class="badge badge-success">
                            {{ lesson_student.check_out_time|time:"H:i:s" }}
                        </span>
                    {% else %}
                        <button class="btn btn-sm btn-outline w-full"
                                {% if not lesson_student.check_in_time %}disabled{% endif %}
                                hx-post="{% url 'attendance:check_out' lesson_id student_id %}"
                                hx-target="#checkout-display-{{ student_id }}"
                                hx-swap="innerHTML">
                            <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>
                            </svg>
                            Wyjście
                        </button>
                    {% endif %}
                </div>
            </div>
        </div>

        <!-- Duration -->
        {% if lesson_student.check_in_time and lesson_student.check_out_time %}
        <div class="mt-4 pt-4 border-t text-center">
            <div class="text-sm text-base-content/70">
                Czas trwania: <strong>{{ duration_minutes }} min</strong>
            </div>
        </div>
        {% endif %}
    </div>
</div>
```

### Group Attendance Table View

**File**: `templates/attendance/partials/_group_attendance.html`

```html
<div class="overflow-x-auto">
    <table class="table table-zebra">
        <thead>
            <tr>
                <th>
                    <label>
                        <input type="checkbox"
                               class="checkbox checkbox-sm"
                               id="select-all"
                               onchange="toggleSelectAll(this)">
                    </label>
                </th>
                <th>Uczeń</th>
                <th>Klasa</th>
                <th>Status</th>
                <th>Akcje</th>
            </tr>
        </thead>
        <tbody>
            {% for ls in students %}
            <tr>
                <td>
                    <label>
                        <input type="checkbox"
                               class="checkbox checkbox-sm student-checkbox"
                               value="{{ ls.student.id }}"
                               onchange="updateBulkActions()">
                    </label>
                </td>
                <td>
                    <div>
                        <div class="font-medium">{{ ls.student.get_full_name }}</div>
                        <div class="text-sm text-base-content/60">{{ ls.student.email }}</div>
                    </div>
                </td>
                <td>{{ ls.student.student_profile.class_name|default:"N/A" }}</td>
                <td>
                    {% include "attendance/partials/_status_badge.html" with status=ls.attendance_status %}
                </td>
                <td>
                    <div class="flex gap-1">
                        <button class="btn btn-xs btn-success"
                                hx-post="{% url 'attendance:mark' lesson.pk %}"
                                hx-vals='{"student_id": "{{ ls.student.id }}", "status": "PRESENT"}'
                                hx-target="#status-{{ ls.student.id }}"
                                hx-swap="outerHTML">
                            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                            </svg>
                        </button>
                        <button class="btn btn-xs btn-error"
                                hx-post="{% url 'attendance:mark' lesson.pk %}"
                                hx-vals='{"student_id": "{{ ls.student.id }}", "status": "ABSENT"}'
                                hx-target="#status-{{ ls.student.id }}"
                                hx-swap="outerHTML">
                            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                            </svg>
                        </button>
                        <button class="btn btn-xs btn-warning"
                                hx-post="{% url 'attendance:mark' lesson.pk %}"
                                hx-vals='{"student_id": "{{ ls.student.id }}", "status": "LATE"}'
                                hx-target="#status-{{ ls.student.id }}"
                                hx-swap="outerHTML">
                            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                            </svg>
                        </button>
                    </div>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>

<!-- Bulk Actions Bar (shown when items selected) -->
<div id="bulk-actions" class="hidden fixed bottom-4 left-1/2 -translate-x-1/2 bg-primary text-primary-content rounded-lg shadow-lg p-4 flex items-center gap-4">
    <span id="selected-count">0</span> zaznaczonych
    <div class="flex gap-2">
        <button class="btn btn-sm btn-success" onclick="bulkMark('PRESENT')">Obecni</button>
        <button class="btn btn-sm btn-error" onclick="bulkMark('ABSENT')">Nieobecni</button>
        <button class="btn btn-sm btn-warning" onclick="bulkMark('LATE')">Spóźnieni</button>
    </div>
</div>

<script>
function toggleSelectAll(checkbox) {
    document.querySelectorAll('.student-checkbox').forEach(cb => {
        cb.checked = checkbox.checked;
    });
    updateBulkActions();
}

function updateBulkActions() {
    const checked = document.querySelectorAll('.student-checkbox:checked');
    const bulkBar = document.getElementById('bulk-actions');
    const countSpan = document.getElementById('selected-count');

    if (checked.length > 0) {
        bulkBar.classList.remove('hidden');
        countSpan.textContent = checked.length;
    } else {
        bulkBar.classList.add('hidden');
    }
}

function bulkMark(status) {
    const checked = document.querySelectorAll('.student-checkbox:checked');
    const studentIds = Array.from(checked).map(cb => cb.value);

    // Send bulk update via HTMX
    htmx.ajax('POST', '{% url "attendance:bulk_mark" lesson.pk %}', {
        values: {
            csrfmiddlewaretoken: '{{ csrf_token }}',
            ...Object.fromEntries(studentIds.map(id => [`status_${id}`, status]))
        }
    });
}
</script>
```

### Status Badge Component

**File**: `templates/attendance/partials/_status_badge.html`

```html
{% if status == 'PRESENT' %}
<span class="badge badge-success gap-1" id="status-{{ student_id }}">
    <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
    </svg>
    Obecny
</span>
{% elif status == 'ABSENT' %}
<span class="badge badge-error gap-1" id="status-{{ student_id }}">
    <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
    </svg>
    Nieobecny
</span>
{% elif status == 'LATE' %}
<span class="badge badge-warning gap-1" id="status-{{ student_id }}">
    <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
    </svg>
    Spóźniony
</span>
{% elif status == 'EXCUSED' %}
<span class="badge badge-info gap-1" id="status-{{ student_id }}">
    <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
    </svg>
    Usprawiedliwiony
</span>
{% else %}
<span class="badge badge-ghost gap-1" id="status-{{ student_id }}">
    <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
    </svg>
    Oczekujące
</span>
{% endif %}
```

---

## URL CONFIGURATION

**File**: `apps/attendance/urls.py`

```python
from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    # Attendance marking
    path('lesson/<uuid:lesson_id>/', views.AttendanceMarkingView.as_view(), name='marking'),
    path('lesson/<uuid:lesson_id>/mark/', views.MarkAttendanceAPIView.as_view(), name='mark'),
    path('lesson/<uuid:lesson_id>/bulk/', views.BulkMarkAttendanceView.as_view(), name='bulk_mark'),

    # Time tracking
    path('lesson/<uuid:lesson_id>/student/<uuid:student_id>/check-in/', views.CheckInView.as_view(), name='check_in'),
    path('lesson/<uuid:lesson_id>/student/<uuid:student_id>/check-out/', views.CheckOutView.as_view(), name='check_out'),

    # History
    path('student/<uuid:student_id>/history/', views.AttendanceHistoryView.as_view(), name='history'),
]
```

---

## COMPLETION CHECKLIST

- [ ] Attendance marking UI fully functional
- [ ] AttendanceService implemented
- [ ] All status types working
- [ ] Time tracking (check-in/check-out) operational
- [ ] Group attendance view complete
- [ ] HTMX integration working
- [ ] Database schema supports all features

---

**Next Sprint**: 5.2 - Attendance Statistics & Reports
