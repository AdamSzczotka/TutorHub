# Phase 9 - Sprint 9.2: Student Portal (Django)

## Tasks 113-117: Student Dashboard & Self-Service Features

> **Duration**: Week 13 (Days 3-4, Second part of Phase 9)
> **Goal**: Complete student-facing portal with schedule, cancellations, makeup tracking, and progress view
> **Dependencies**: Sprint 9.1 completed (Tutor Portal), Phase 6 completed (Cancellation System)

---

## SPRINT OVERVIEW

| Task ID | Description                                  | Priority | Dependencies |
| ------- | -------------------------------------------- | -------- | ------------ |
| 113     | Student dashboard with personalized widgets  | Critical | Task 112     |
| 114     | My calendar with color-coded events          | Critical | Task 113     |
| 115     | Cancellation request interface with tracking | High     | Task 114     |
| 116     | Makeup lessons tracker with countdown        | High     | Task 115     |
| 117     | Progress view with stats and achievements    | High     | Task 116     |

---

## STUDENT DASHBOARD SERVICE

### Dashboard Service

**File**: `apps/students/services.py`

```python
from django.db.models import Count, Avg, Q, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from apps.lessons.models import Lesson, LessonStudent
from apps.cancellations.models import CancellationRequest, MakeupLesson
from apps.attendance.models import Attendance


class StudentDashboardService:
    """Service for student dashboard operations."""

    @classmethod
    def get_dashboard_stats(cls, student):
        """Get comprehensive dashboard statistics for student."""
        today = timezone.now().date()
        today_start = timezone.now().replace(hour=0, minute=0, second=0)
        today_end = timezone.now().replace(hour=23, minute=59, second=59)
        month_start = today.replace(day=1)

        # Today's lessons
        today_lessons = LessonStudent.objects.filter(
            student=student,
            lesson__start_time__gte=today_start,
            lesson__start_time__lte=today_end,
            lesson__status__in=['SCHEDULED', 'ONGOING']
        ).select_related('lesson')

        # Next lesson time
        next_lesson = LessonStudent.objects.filter(
            student=student,
            lesson__start_time__gt=timezone.now(),
            lesson__status='SCHEDULED'
        ).select_related('lesson').order_by('lesson__start_time').first()

        # Attendance rate (last 30 days)
        attendance_stats = Attendance.objects.filter(
            student=student,
            lesson__start_time__gte=timezone.now() - timedelta(days=30)
        ).aggregate(
            total=Count('id'),
            present=Count('id', filter=Q(status='PRESENT'))
        )

        attendance_rate = 0
        if attendance_stats['total'] > 0:
            attendance_rate = round(
                (attendance_stats['present'] / attendance_stats['total']) * 100
            )

        # Makeup lessons count
        makeup_count = MakeupLesson.objects.filter(
            original_lesson__lessonstudent__student=student,
            status='PENDING',
            expires_at__gt=timezone.now()
        ).count()

        # Achievements count (placeholder - implement if needed)
        achievements_count = cls._calculate_achievements(student)

        return {
            'today_lessons_count': today_lessons.count(),
            'next_lesson_time': next_lesson.lesson.start_time.strftime('%H:%M') if next_lesson else None,
            'attendance_rate': attendance_rate,
            'makeup_count': makeup_count,
            'achievements_count': achievements_count,
        }

    @classmethod
    def get_today_lessons(cls, student):
        """Get today's lessons for student."""
        today_start = timezone.now().replace(hour=0, minute=0, second=0)
        today_end = timezone.now().replace(hour=23, minute=59, second=59)

        return LessonStudent.objects.filter(
            student=student,
            lesson__start_time__gte=today_start,
            lesson__start_time__lte=today_end
        ).select_related(
            'lesson',
            'lesson__tutor',
            'lesson__subject',
            'lesson__room'
        ).order_by('lesson__start_time')

    @classmethod
    def get_upcoming_lessons(cls, student, limit=5):
        """Get upcoming lessons for student."""
        return LessonStudent.objects.filter(
            student=student,
            lesson__start_time__gt=timezone.now(),
            lesson__status='SCHEDULED'
        ).select_related(
            'lesson',
            'lesson__tutor',
            'lesson__subject',
            'lesson__room'
        ).order_by('lesson__start_time')[:limit]

    @classmethod
    def get_makeup_lessons(cls, student):
        """Get pending makeup lessons for student."""
        return MakeupLesson.objects.filter(
            original_lesson__lessonstudent__student=student,
            status='PENDING',
            expires_at__gt=timezone.now()
        ).select_related(
            'original_lesson',
            'original_lesson__subject',
            'original_lesson__tutor'
        ).order_by('expires_at')

    @classmethod
    def get_recent_progress(cls, student, limit=3):
        """Get recent progress notes for student."""
        return Attendance.objects.filter(
            student=student,
            notes__isnull=False
        ).exclude(notes='').select_related(
            'lesson',
            'lesson__subject'
        ).order_by('-lesson__start_time')[:limit]

    @classmethod
    def _calculate_achievements(cls, student):
        """Calculate unlocked achievements for student."""
        achievements = 0

        # Achievement: First lesson attended
        if Attendance.objects.filter(student=student, status='PRESENT').exists():
            achievements += 1

        # Achievement: 10 lessons completed
        if Attendance.objects.filter(student=student, status='PRESENT').count() >= 10:
            achievements += 1

        # Achievement: 100% attendance in a month
        # (simplified check)
        achievements += 1  # placeholder

        return achievements


class StudentProgressService:
    """Service for student progress tracking."""

    @classmethod
    def get_progress_stats(cls, student):
        """Get overall progress statistics."""
        thirty_days_ago = timezone.now() - timedelta(days=30)

        # Attendance stats
        attendance = Attendance.objects.filter(student=student)
        total_lessons = attendance.count()
        completed_lessons = attendance.filter(status='PRESENT').count()

        attendance_rate = 0
        if total_lessons > 0:
            attendance_rate = round((completed_lessons / total_lessons) * 100)

        # Hours calculation
        total_hours = LessonStudent.objects.filter(
            student=student,
            lesson__status='COMPLETED'
        ).aggregate(
            total=Sum('lesson__duration_minutes')
        )['total'] or 0

        monthly_hours = LessonStudent.objects.filter(
            student=student,
            lesson__status='COMPLETED',
            lesson__start_time__gte=thirty_days_ago
        ).aggregate(
            total=Sum('lesson__duration_minutes')
        )['total'] or 0

        return {
            'attendance_rate': attendance_rate,
            'completed_lessons': completed_lessons,
            'total_lessons': total_lessons,
            'total_hours': round(total_hours / 60, 1),
            'monthly_hours': round(monthly_hours / 60, 1),
        }

    @classmethod
    def get_subject_progress(cls, student):
        """Get progress breakdown by subject."""
        from apps.subjects.models import Subject

        subjects = Subject.objects.filter(
            lessons__lessonstudent__student=student
        ).distinct()

        result = []
        for subject in subjects:
            lessons = LessonStudent.objects.filter(
                student=student,
                lesson__subject=subject
            )
            total = lessons.count()
            completed = lessons.filter(lesson__status='COMPLETED').count()

            # Average score from attendance notes (if tracked)
            avg_score = 75  # placeholder

            result.append({
                'id': str(subject.id),
                'name': subject.name,
                'color': subject.color,
                'total_lessons': total,
                'completed_lessons': completed,
                'avg_score': avg_score,
            })

        return result

    @classmethod
    def get_achievements(cls, student):
        """Get student achievements."""
        badges = [
            {
                'id': 'first_lesson',
                'name': 'Pierwsza lekcja',
                'icon': '🎓',
                'unlocked': Attendance.objects.filter(
                    student=student, status='PRESENT'
                ).exists(),
                'unlocked_at': Attendance.objects.filter(
                    student=student, status='PRESENT'
                ).order_by('created_at').first().created_at if Attendance.objects.filter(
                    student=student, status='PRESENT'
                ).exists() else None,
            },
            {
                'id': 'ten_lessons',
                'name': '10 lekcji',
                'icon': '📚',
                'unlocked': Attendance.objects.filter(
                    student=student, status='PRESENT'
                ).count() >= 10,
                'unlocked_at': None,
            },
            {
                'id': 'perfect_month',
                'name': 'Idealny miesiąc',
                'icon': '⭐',
                'unlocked': False,
                'unlocked_at': None,
            },
            {
                'id': 'early_bird',
                'name': 'Ranny ptaszek',
                'icon': '🐦',
                'unlocked': False,
                'unlocked_at': None,
            },
        ]

        unlocked_count = sum(1 for b in badges if b['unlocked'])

        return {
            'unlocked': unlocked_count,
            'total': len(badges),
            'badges': badges,
        }


class StudentCancellationService:
    """Service for student cancellation operations."""

    @classmethod
    def get_cancellation_limit(cls, student):
        """Get monthly cancellation limit and usage."""
        from apps.core.models import SystemSetting

        month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0)
        limit = SystemSetting.get('monthly_cancellation_limit', 3)

        used = CancellationRequest.objects.filter(
            student=student,
            created_at__gte=month_start,
            status__in=['PENDING', 'APPROVED']
        ).count()

        return {
            'limit': limit,
            'used': used,
            'remaining': max(0, limit - used),
        }

    @classmethod
    def can_cancel_lesson(cls, student, lesson):
        """Check if student can cancel a lesson."""
        from datetime import timedelta

        # Check 24h rule
        hours_until = (lesson.start_time - timezone.now()).total_seconds() / 3600
        if hours_until < 24:
            return False, 'Anulowanie możliwe minimum 24h przed zajęciami'

        # Check monthly limit
        limit_info = cls.get_cancellation_limit(student)
        if limit_info['remaining'] <= 0:
            return False, 'Przekroczono miesięczny limit anulowań'

        # Check if already has pending request
        existing = CancellationRequest.objects.filter(
            student=student,
            lesson=lesson,
            status='PENDING'
        ).exists()
        if existing:
            return False, 'Już złożono wniosek o anulowanie tych zajęć'

        return True, None

    @classmethod
    def create_cancellation_request(cls, student, lesson, reason):
        """Create a cancellation request."""
        can_cancel, error = cls.can_cancel_lesson(student, lesson)
        if not can_cancel:
            raise ValueError(error)

        request = CancellationRequest.objects.create(
            student=student,
            lesson=lesson,
            reason=reason,
            status='PENDING'
        )

        # Send notification to admin
        from apps.notifications.services import NotificationService
        NotificationService.notify_admins(
            title='Nowy wniosek o anulowanie',
            message=f'{student.get_full_name()} prosi o anulowanie zajęć: {lesson.title}',
            notification_type='CANCELLATION_REQUEST',
            related_object=request
        )

        return request
```

---

## STUDENT VIEWS

### Dashboard Views

**File**: `apps/students/views.py`

```python
from django.views.generic import TemplateView, ListView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta

from apps.core.mixins import StudentRequiredMixin, HTMXMixin
from apps.lessons.models import Lesson, LessonStudent
from apps.cancellations.models import CancellationRequest, MakeupLesson
from .services import (
    StudentDashboardService,
    StudentProgressService,
    StudentCancellationService
)
from .forms import CancellationRequestForm


class StudentDashboardView(LoginRequiredMixin, StudentRequiredMixin, HTMXMixin, TemplateView):
    """Student dashboard with personalized widgets."""
    template_name = 'student_panel/dashboard.html'
    partial_template_name = 'student_panel/partials/_dashboard_content.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.request.user

        context['stats'] = StudentDashboardService.get_dashboard_stats(student)
        context['today_lessons'] = StudentDashboardService.get_today_lessons(student)
        context['upcoming_lessons'] = StudentDashboardService.get_upcoming_lessons(student)
        context['makeup_lessons'] = StudentDashboardService.get_makeup_lessons(student)
        context['recent_progress'] = StudentDashboardService.get_recent_progress(student)
        context['today'] = timezone.now()

        return context


class StudentCalendarView(LoginRequiredMixin, StudentRequiredMixin, TemplateView):
    """Student calendar page with FullCalendar."""
    template_name = 'student_panel/calendar.html'


class StudentCalendarEventsView(LoginRequiredMixin, StudentRequiredMixin, TemplateView):
    """API endpoint for student calendar events."""

    def get(self, request):
        import json
        from django.http import JsonResponse

        student = request.user
        start = request.GET.get('start')
        end = request.GET.get('end')

        lessons = LessonStudent.objects.filter(
            student=student
        ).select_related(
            'lesson', 'lesson__subject', 'lesson__tutor', 'lesson__room'
        )

        if start:
            lessons = lessons.filter(lesson__start_time__gte=start)
        if end:
            lessons = lessons.filter(lesson__end_time__lte=end)

        events = []
        for ls in lessons:
            lesson = ls.lesson
            color = cls._get_status_color(lesson.status)

            events.append({
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
                }
            })

        return JsonResponse(events, safe=False)

    @staticmethod
    def _get_status_color(status):
        colors = {
            'SCHEDULED': '#3B82F6',  # blue
            'ONGOING': '#10B981',    # green
            'COMPLETED': '#6B7280',  # gray
            'CANCELLED': '#EF4444',  # red
        }
        return colors.get(status, '#3B82F6')


class StudentLessonDetailView(LoginRequiredMixin, StudentRequiredMixin, HTMXMixin, DetailView):
    """Student lesson detail modal."""
    model = Lesson
    template_name = 'student_panel/partials/_lesson_detail.html'
    context_object_name = 'lesson'

    def get_queryset(self):
        return Lesson.objects.filter(
            lessonstudent__student=self.request.user
        ).select_related('tutor', 'subject', 'room')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lesson = self.object

        # Check if can cancel
        can_cancel, _ = StudentCancellationService.can_cancel_lesson(
            self.request.user, lesson
        )
        context['can_cancel'] = can_cancel and lesson.status == 'SCHEDULED'
        context['hours_until'] = (lesson.start_time - timezone.now()).total_seconds() / 3600

        return context


class CancellationRequestListView(LoginRequiredMixin, StudentRequiredMixin, HTMXMixin, TemplateView):
    """Student cancellation requests page."""
    template_name = 'student_panel/cancellations/list.html'
    partial_template_name = 'student_panel/cancellations/partials/_request_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.request.user

        # Get cancellable lessons
        context['upcoming_lessons'] = LessonStudent.objects.filter(
            student=student,
            lesson__start_time__gt=timezone.now() + timedelta(hours=24),
            lesson__status='SCHEDULED'
        ).select_related('lesson', 'lesson__subject', 'lesson__tutor')

        # Get existing requests
        context['requests'] = CancellationRequest.objects.filter(
            student=student
        ).select_related('lesson', 'lesson__subject').order_by('-created_at')[:10]

        # Get limit info
        context['limit_info'] = StudentCancellationService.get_cancellation_limit(student)

        # Pre-selected lesson (if from calendar)
        event_id = self.request.GET.get('eventId')
        if event_id:
            context['preselected_lesson_id'] = event_id

        return context


class CancellationRequestCreateView(LoginRequiredMixin, StudentRequiredMixin, CreateView):
    """Create cancellation request via HTMX."""
    model = CancellationRequest
    form_class = CancellationRequestForm
    template_name = 'student_panel/cancellations/partials/_request_form.html'

    def form_valid(self, form):
        student = self.request.user
        lesson = form.cleaned_data['lesson']
        reason = form.cleaned_data['reason']

        try:
            StudentCancellationService.create_cancellation_request(
                student=student,
                lesson=lesson,
                reason=reason
            )

            return HttpResponse(
                status=204,
                headers={
                    'HX-Trigger': 'cancellationCreated',
                    'HX-Reswap': 'none',
                }
            )
        except ValueError as e:
            form.add_error(None, str(e))
            return self.form_invalid(form)

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))


class MakeupLessonsListView(LoginRequiredMixin, StudentRequiredMixin, HTMXMixin, TemplateView):
    """Student makeup lessons tracker."""
    template_name = 'student_panel/makeup/list.html'
    partial_template_name = 'student_panel/makeup/partials/_makeup_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.request.user
        today = timezone.now()

        makeup_lessons = MakeupLesson.objects.filter(
            original_lesson__lessonstudent__student=student
        ).select_related(
            'original_lesson',
            'original_lesson__subject',
            'original_lesson__tutor'
        ).order_by('expires_at')

        # Add computed fields
        for makeup in makeup_lessons:
            days_left = (makeup.expires_at - today).days
            makeup.days_left = max(0, days_left)
            makeup.progress = min(100, ((30 - days_left) / 30) * 100)
            makeup.is_expiring_soon = days_left <= 7 and days_left >= 0
            makeup.is_expired = days_left < 0

        context['makeup_lessons'] = makeup_lessons
        context['expiring_soon_count'] = sum(
            1 for m in makeup_lessons if m.is_expiring_soon
        )

        return context


class StudentProgressView(LoginRequiredMixin, StudentRequiredMixin, HTMXMixin, TemplateView):
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
```

---

## STUDENT FORMS

### Cancellation Form

**File**: `apps/students/forms.py`

```python
from django import forms
from apps.cancellations.models import CancellationRequest
from apps.lessons.models import Lesson


class CancellationRequestForm(forms.Form):
    """Form for student cancellation request."""

    lesson = forms.ModelChoiceField(
        queryset=Lesson.objects.none(),
        label='Zajęcia do anulowania',
        widget=forms.Select(attrs={
            'class': 'select select-bordered w-full',
            'hx-get': '',
            'hx-target': '#lesson-details',
            'hx-trigger': 'change',
        })
    )

    reason = forms.CharField(
        label='Powód anulowania',
        min_length=10,
        widget=forms.Textarea(attrs={
            'class': 'textarea textarea-bordered w-full',
            'rows': 4,
            'placeholder': 'Opisz dlaczego chcesz anulować zajęcia...',
        })
    )

    def __init__(self, student=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if student:
            from django.utils import timezone
            from datetime import timedelta

            self.fields['lesson'].queryset = Lesson.objects.filter(
                lessonstudent__student=student,
                start_time__gt=timezone.now() + timedelta(hours=24),
                status='SCHEDULED'
            ).select_related('subject', 'tutor')

    def clean_reason(self):
        reason = self.cleaned_data.get('reason', '')
        if len(reason) < 10:
            raise forms.ValidationError('Podaj powód anulowania (min. 10 znaków)')
        return reason
```

---

## STUDENT TEMPLATES

### Dashboard Template

**File**: `templates/student_panel/dashboard.html`

```html
{% extends "student_panel/base.html" %}

{% block title %}Panel Ucznia - Na Piątkę{% endblock %}

{% block content %}
<div class="space-y-6">
    <!-- Header -->
    <div>
        <h1 class="text-3xl font-bold">Witaj, {{ request.user.first_name }}!</h1>
        <p class="text-gray-600 mt-1">Twój plan zajęć i postępy w nauce</p>
    </div>

    <!-- Stats Cards -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div class="card bg-base-100 shadow">
            <div class="card-body">
                <div class="flex items-center justify-between">
                    <h3 class="text-sm font-medium text-gray-600">Dzisiejsze zajęcia</h3>
                    <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/>
                    </svg>
                </div>
                <div class="text-2xl font-bold">{{ stats.today_lessons_count }}</div>
                <p class="text-xs text-gray-500">
                    {% if stats.next_lesson_time %}
                        Następne o {{ stats.next_lesson_time }}
                    {% else %}
                        Brak zajęć
                    {% endif %}
                </p>
            </div>
        </div>

        <div class="card bg-base-100 shadow">
            <div class="card-body">
                <div class="flex items-center justify-between">
                    <h3 class="text-sm font-medium text-gray-600">Frekwencja</h3>
                    <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                    </svg>
                </div>
                <div class="text-2xl font-bold">{{ stats.attendance_rate }}%</div>
                <progress class="progress progress-success w-full" value="{{ stats.attendance_rate }}" max="100"></progress>
            </div>
        </div>

        <div class="card bg-base-100 shadow">
            <div class="card-body">
                <div class="flex items-center justify-between">
                    <h3 class="text-sm font-medium text-gray-600">Do odrobienia</h3>
                    <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                    </svg>
                </div>
                <div class="text-2xl font-bold">{{ stats.makeup_count }}</div>
                <p class="text-xs text-gray-500">zajęć do przeprowadzenia</p>
            </div>
        </div>

        <div class="card bg-base-100 shadow">
            <div class="card-body">
                <div class="flex items-center justify-between">
                    <h3 class="text-sm font-medium text-gray-600">Osiągnięcia</h3>
                    <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"/>
                    </svg>
                </div>
                <div class="text-2xl font-bold">{{ stats.achievements_count }}</div>
                <p class="text-xs text-gray-500">odblokowanych odznak</p>
            </div>
        </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Today's Schedule -->
        <div class="lg:col-span-2">
            <div class="card bg-base-100 shadow">
                <div class="card-body">
                    <h2 class="card-title">Dzisiejszy plan</h2>
                    <p class="text-sm text-gray-600">{{ today|date:"l, j F Y" }}</p>

                    {% if today_lessons %}
                        <div class="space-y-3 mt-4">
                            {% for ls in today_lessons %}
                                {% with lesson=ls.lesson %}
                                <div class="flex items-start gap-4 p-4 border rounded-lg hover:bg-base-200 transition-colors">
                                    <div class="w-1 self-stretch rounded-full"
                                         style="background-color: {{ lesson.subject.color|default:'#3B82F6' }}"></div>

                                    <div class="flex-1 min-w-0">
                                        <div class="flex items-center gap-2 mb-1">
                                            <h4 class="font-medium">{{ lesson.title }}</h4>
                                            {% if lesson.is_ongoing %}
                                                <span class="badge badge-primary animate-pulse">Teraz</span>
                                            {% elif lesson.status == 'COMPLETED' %}
                                                <span class="badge badge-ghost">Zakończone</span>
                                            {% endif %}
                                        </div>

                                        <div class="text-sm text-gray-600 space-y-1">
                                            <div class="flex items-center gap-4">
                                                <span>{{ lesson.start_time|time:"H:i" }} - {{ lesson.end_time|time:"H:i" }}</span>
                                                <span>{{ lesson.tutor.get_full_name }}</span>
                                            </div>
                                            <div class="flex items-center gap-4">
                                                <span>{{ lesson.subject.name }}</span>
                                                <span>{{ lesson.room.name|default:"Online" }}</span>
                                            </div>
                                        </div>

                                        {% if lesson.description %}
                                            <p class="text-sm text-gray-500 mt-2 line-clamp-2">{{ lesson.description }}</p>
                                        {% endif %}
                                    </div>

                                    {% if lesson.status == 'SCHEDULED' %}
                                        <button class="btn btn-outline btn-sm"
                                                hx-get="{% url 'students:lesson-detail' lesson.pk %}"
                                                hx-target="#modal-content"
                                                onclick="document.getElementById('modal').showModal()">
                                            Szczegóły
                                        </button>
                                    {% endif %}
                                </div>
                                {% endwith %}
                            {% endfor %}
                        </div>
                    {% else %}
                        <div class="text-center py-8 text-gray-500">
                            <svg class="w-12 h-12 mx-auto mb-2 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/>
                            </svg>
                            <p>Brak zajęć na dzisiaj</p>
                            <p class="text-sm mt-1">Możesz odpocząć!</p>
                        </div>
                    {% endif %}
                </div>
            </div>
        </div>

        <!-- Sidebar -->
        <div class="space-y-6">
            <!-- Upcoming Lessons -->
            <div class="card bg-base-100 shadow">
                <div class="card-body">
                    <h2 class="card-title text-lg">Nadchodzące zajęcia</h2>

                    {% if upcoming_lessons %}
                        <div class="space-y-2">
                            {% for ls in upcoming_lessons %}
                                {% with lesson=ls.lesson %}
                                <div class="flex items-center justify-between p-3 border rounded-lg text-sm">
                                    <div class="flex-1 min-w-0">
                                        <div class="font-medium truncate">{{ lesson.title }}</div>
                                        <div class="text-xs text-gray-600">
                                            {{ lesson.start_time|date:"j M, H:i" }}
                                        </div>
                                    </div>
                                    <div class="w-2 h-2 rounded-full ml-2"
                                         style="background-color: {{ lesson.subject.color|default:'#3B82F6' }}"></div>
                                </div>
                                {% endwith %}
                            {% endfor %}

                            <a href="{% url 'students:calendar' %}" class="btn btn-outline btn-block mt-2">
                                Cały kalendarz
                            </a>
                        </div>
                    {% else %}
                        <div class="text-center py-6 text-gray-500 text-sm">
                            Brak zaplanowanych zajęć
                        </div>
                    {% endif %}
                </div>
            </div>

            <!-- Makeup Lessons Alert -->
            {% if makeup_lessons %}
                <div class="card bg-warning/10 border border-warning shadow">
                    <div class="card-body">
                        <h2 class="card-title text-lg text-warning-content flex items-center gap-2">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
                            </svg>
                            Zajęcia do odrobienia
                        </h2>

                        <p class="text-sm text-warning-content/80 mb-3">
                            Masz {{ makeup_lessons|length }} zajęć do przeprowadzenia
                        </p>

                        {% for makeup in makeup_lessons|slice:":2" %}
                            <div class="bg-base-100 border border-warning/30 rounded p-2 mb-2 text-sm">
                                <div class="font-medium">{{ makeup.original_lesson.title }}</div>
                                <div class="text-xs text-gray-600">
                                    Wygasa: {{ makeup.expires_at|date:"j M Y" }}
                                </div>
                            </div>
                        {% endfor %}

                        <a href="{% url 'students:makeup-list' %}" class="btn btn-outline btn-warning btn-block mt-2">
                            Zaplanuj zajęcia zastępcze
                        </a>
                    </div>
                </div>
            {% endif %}
        </div>
    </div>

    <!-- Recent Progress -->
    {% if recent_progress %}
        <div class="card bg-base-100 shadow">
            <div class="card-body">
                <h2 class="card-title">Ostatnie postępy</h2>
                <p class="text-sm text-gray-600">Twoje ostatnie oceny i notatki od korepetytorów</p>

                <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
                    {% for attendance in recent_progress %}
                        <div class="border rounded-lg p-4">
                            <div class="flex items-center justify-between mb-2">
                                <div class="font-medium">{{ attendance.lesson.subject.name }}</div>
                                <span class="badge badge-primary">75/100</span>
                            </div>

                            {% if attendance.notes %}
                                <p class="text-sm text-gray-600 line-clamp-2">{{ attendance.notes }}</p>
                            {% endif %}

                            <div class="text-xs text-gray-500 mt-2">
                                {{ attendance.lesson.start_time|date:"j M Y" }}
                            </div>
                        </div>
                    {% endfor %}
                </div>

                <a href="{% url 'students:progress' %}" class="btn btn-outline btn-block mt-4">
                    <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/>
                    </svg>
                    Zobacz wszystkie postępy
                </a>
            </div>
        </div>
    {% endif %}

    <!-- Quick Actions -->
    <div class="card bg-base-100 shadow">
        <div class="card-body">
            <h2 class="card-title">Szybkie akcje</h2>

            <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mt-2">
                <a href="{% url 'students:calendar' %}" class="btn btn-outline h-auto flex-col py-4">
                    <svg class="w-6 h-6 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/>
                    </svg>
                    Kalendarz
                </a>

                <a href="{% url 'students:cancellation-list' %}" class="btn btn-outline h-auto flex-col py-4">
                    <svg class="w-6 h-6 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
                    </svg>
                    Anuluj zajęcia
                </a>

                <a href="{% url 'students:makeup-list' %}" class="btn btn-outline h-auto flex-col py-4">
                    <svg class="w-6 h-6 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                    </svg>
                    Odrobienie
                </a>

                <a href="{% url 'students:progress' %}" class="btn btn-outline h-auto flex-col py-4">
                    <svg class="w-6 h-6 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/>
                    </svg>
                    Postępy
                </a>
            </div>
        </div>
    </div>
</div>

<!-- Modal -->
<dialog id="modal" class="modal">
    <div class="modal-box max-w-md">
        <div id="modal-content"></div>
    </div>
    <form method="dialog" class="modal-backdrop">
        <button>close</button>
    </form>
</dialog>
{% endblock %}
```

### Cancellation Request Form Partial

**File**: `templates/student_panel/cancellations/partials/_request_form.html`

```html
<form hx-post="{% url 'students:cancellation-create' %}"
      hx-target="this"
      hx-swap="outerHTML"
      class="space-y-6">
    {% csrf_token %}

    <!-- Monthly Limit Info -->
    {% if limit_info %}
        <div class="alert alert-info">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
            <span>Wykorzystano {{ limit_info.used }} z {{ limit_info.limit }} dostępnych anulowań w tym miesiącu</span>
        </div>
    {% endif %}

    {% if limit_info.remaining <= 0 %}
        <div class="alert alert-error">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
            </svg>
            <span>Osiągnięto miesięczny limit anulowań. Skontaktuj się z administracją w wyjątkowych sytuacjach.</span>
        </div>
    {% endif %}

    <!-- Lesson Selection -->
    <div class="form-control">
        <label class="label">
            <span class="label-text">Wybierz zajęcia do anulowania *</span>
        </label>
        <select name="lesson"
                class="select select-bordered w-full"
                x-data="{ selected: '{{ preselected_lesson_id|default:'' }}' }"
                x-model="selected"
                hx-get="{% url 'students:lesson-detail' 0 %}"
                hx-target="#lesson-details"
                hx-trigger="change"
                hx-vals='js:{"pk": this.value}'
                required>
            <option value="">Wybierz zajęcia</option>
            {% for ls in upcoming_lessons %}
                {% with lesson=ls.lesson %}
                <option value="{{ lesson.id }}" {% if lesson.id|stringformat:"s" == preselected_lesson_id %}selected{% endif %}>
                    {{ lesson.title }} - {{ lesson.start_time|date:"j M, H:i" }}
                </option>
                {% endwith %}
            {% endfor %}
        </select>
        <label class="label">
            <span class="label-text-alt">Możesz anulować zajęcia minimum 24 godziny przed ich rozpoczęciem</span>
        </label>
        {% if form.lesson.errors %}
            <label class="label">
                <span class="label-text-alt text-error">{{ form.lesson.errors.0 }}</span>
            </label>
        {% endif %}
    </div>

    <!-- Selected Lesson Details -->
    <div id="lesson-details"></div>

    <!-- Reason -->
    <div class="form-control">
        <label class="label">
            <span class="label-text">Powód anulowania *</span>
        </label>
        <textarea name="reason"
                  class="textarea textarea-bordered w-full"
                  rows="4"
                  placeholder="Opisz dlaczego chcesz anulować zajęcia..."
                  minlength="10"
                  required>{{ form.reason.value|default:'' }}</textarea>
        <label class="label">
            <span class="label-text-alt">Podaj krótki powód anulowania (minimum 10 znaków)</span>
        </label>
        {% if form.reason.errors %}
            <label class="label">
                <span class="label-text-alt text-error">{{ form.reason.errors.0 }}</span>
            </label>
        {% endif %}
    </div>

    <!-- Info Alert -->
    <div class="alert">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
        </svg>
        <div>
            <strong>Pamiętaj:</strong> Po zaakceptowaniu anulowania przez administrację,
            zajęcia zostaną dodane do puli zajęć do odrobienia. Będziesz miał 30 dni
            na umówienie się na zajęcia zastępcze.
        </div>
    </div>

    <!-- Form Errors -->
    {% if form.non_field_errors %}
        <div class="alert alert-error">
            {% for error in form.non_field_errors %}
                <span>{{ error }}</span>
            {% endfor %}
        </div>
    {% endif %}

    <!-- Actions -->
    <div class="flex justify-end gap-2">
        <button type="reset" class="btn btn-ghost">Wyczyść</button>
        <button type="submit"
                class="btn btn-primary"
                {% if limit_info.remaining <= 0 %}disabled{% endif %}>
            Wyślij wniosek
        </button>
    </div>
</form>
```

### Makeup Lessons List Partial

**File**: `templates/student_panel/makeup/partials/_makeup_list.html`

```html
{% if expiring_soon_count > 0 %}
    <div class="alert alert-error mb-6">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
        </svg>
        <div>
            <strong>Uwaga!</strong> {{ expiring_soon_count }} zajęć wygasa w ciągu najbliższych 7 dni.
            Zaplanuj je jak najszybciej!
        </div>
    </div>
{% endif %}

{% if makeup_lessons %}
    <div class="space-y-4">
        {% for makeup in makeup_lessons %}
            <div class="card bg-base-100 shadow {% if makeup.is_expiring_soon %}border-2 border-warning{% endif %}">
                <div class="card-body">
                    <div class="flex items-start justify-between">
                        <div class="flex-1">
                            <h3 class="card-title text-lg">{{ makeup.original_lesson.title }}</h3>
                            <p class="text-sm text-gray-600">
                                Przedmiot: {{ makeup.original_lesson.subject.name }}
                            </p>
                        </div>

                        {% if makeup.is_expired %}
                            <span class="badge badge-error">Wygasło</span>
                        {% elif makeup.is_expiring_soon %}
                            <span class="badge badge-warning">Pilne</span>
                        {% else %}
                            <span class="badge badge-ghost">Do odrobienia</span>
                        {% endif %}
                    </div>

                    <div class="grid grid-cols-2 gap-4 mt-4 text-sm">
                        <div>
                            <div class="text-gray-600">Pierwotny termin</div>
                            <div class="font-medium">{{ makeup.original_lesson.start_time|date:"j M Y, H:i" }}</div>
                        </div>
                        <div>
                            <div class="text-gray-600">Korepetytor</div>
                            <div class="font-medium">{{ makeup.original_lesson.tutor.get_full_name }}</div>
                        </div>
                    </div>

                    <div class="mt-4">
                        <div class="flex items-center justify-between text-sm mb-2">
                            <span class="text-gray-600">
                                {% if makeup.is_expired %}
                                    Zajęcia wygasły
                                {% else %}
                                    Pozostało {{ makeup.days_left }} dni (do {{ makeup.expires_at|date:"j M" }})
                                {% endif %}
                            </span>
                            <span class="font-medium {% if makeup.is_expiring_soon %}text-error{% endif %}">
                                {{ makeup.days_left }}/30 dni
                            </span>
                        </div>
                        <progress class="progress {% if makeup.is_expiring_soon %}progress-error{% else %}progress-primary{% endif %} w-full"
                                  value="{{ makeup.progress|floatformat:0 }}"
                                  max="100"></progress>
                    </div>

                    {% if makeup.reason %}
                        <div class="bg-base-200 rounded-lg p-3 mt-4 text-sm">
                            <div class="text-gray-600 mb-1">Powód anulowania:</div>
                            <div>{{ makeup.reason }}</div>
                        </div>
                    {% endif %}

                    {% if not makeup.is_expired %}
                        <div class="flex items-center gap-2 mt-4">
                            <a href="{% url 'students:makeup-schedule' makeup.id %}" class="btn btn-primary flex-1">
                                <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/>
                                </svg>
                                Zaplanuj zajęcia
                            </a>

                            {% if makeup.days_left <= 7 %}
                                <a href="{% url 'messaging:compose' %}?subject=Przedłużenie terminu" class="btn btn-outline flex-1">
                                    Poproś o przedłużenie
                                </a>
                            {% endif %}
                        </div>
                    {% else %}
                        <div class="alert mt-4">
                            <span class="text-sm">
                                Te zajęcia wygasły. Skontaktuj się z administracją jeśli potrzebujesz dodatkowych informacji.
                            </span>
                        </div>
                    {% endif %}
                </div>
            </div>
        {% endfor %}
    </div>
{% else %}
    <div class="card bg-base-100 shadow">
        <div class="card-body py-12 text-center text-gray-500">
            <svg class="w-12 h-12 mx-auto mb-3 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
            <p class="text-lg font-medium">Brak zajęć do odrobienia</p>
            <p class="text-sm mt-1">Świetnie! Nie masz żadnych zaległych zajęć.</p>
        </div>
    </div>
{% endif %}
```

### Progress Page Template

**File**: `templates/student_panel/progress/index.html`

```html
{% extends "student_panel/base.html" %}

{% block title %}Moje postępy - Na Piątkę{% endblock %}

{% block content %}
<div class="space-y-6">
    <!-- Header -->
    <div>
        <h1 class="text-3xl font-bold">Moje postępy</h1>
        <p class="text-gray-600 mt-1">Śledź swoją naukę i osiągnięcia</p>
    </div>

    <!-- Stats Overview -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div class="card bg-base-100 shadow">
            <div class="card-body">
                <div class="flex items-center justify-between">
                    <h3 class="text-sm font-medium text-gray-600">Frekwencja</h3>
                    <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/>
                    </svg>
                </div>
                <div class="text-2xl font-bold">{{ stats.attendance_rate }}%</div>
                <progress class="progress progress-success w-full" value="{{ stats.attendance_rate }}" max="100"></progress>
            </div>
        </div>

        <div class="card bg-base-100 shadow">
            <div class="card-body">
                <div class="flex items-center justify-between">
                    <h3 class="text-sm font-medium text-gray-600">Zajęć ukończonych</h3>
                    <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                    </svg>
                </div>
                <div class="text-2xl font-bold">{{ stats.completed_lessons }}</div>
                <p class="text-xs text-gray-500">z {{ stats.total_lessons }} zaplanowanych</p>
            </div>
        </div>

        <div class="card bg-base-100 shadow">
            <div class="card-body">
                <div class="flex items-center justify-between">
                    <h3 class="text-sm font-medium text-gray-600">Godzin nauki</h3>
                    <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                    </svg>
                </div>
                <div class="text-2xl font-bold">{{ stats.total_hours }}h</div>
                <p class="text-xs text-gray-500">w tym miesiącu: {{ stats.monthly_hours }}h</p>
            </div>
        </div>

        <div class="card bg-base-100 shadow">
            <div class="card-body">
                <div class="flex items-center justify-between">
                    <h3 class="text-sm font-medium text-gray-600">Osiągnięcia</h3>
                    <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"/>
                    </svg>
                </div>
                <div class="text-2xl font-bold">{{ achievements.unlocked }}</div>
                <p class="text-xs text-gray-500">z {{ achievements.total }} dostępnych</p>
            </div>
        </div>
    </div>

    <!-- Progress by Subject -->
    <div class="card bg-base-100 shadow">
        <div class="card-body">
            <h2 class="card-title">Postępy według przedmiotów</h2>
            <p class="text-sm text-gray-600">Twoje wyniki w poszczególnych przedmiotach</p>

            {% if subjects %}
                <div class="space-y-4 mt-4">
                    {% for subject in subjects %}
                        <div class="space-y-2">
                            <div class="flex items-center justify-between">
                                <div class="flex items-center gap-2">
                                    <div class="w-3 h-3 rounded-full" style="background-color: {{ subject.color }}"></div>
                                    <span class="font-medium">{{ subject.name }}</span>
                                </div>
                                <div class="flex items-center gap-4 text-sm">
                                    <span class="text-gray-600">
                                        {{ subject.completed_lessons }} / {{ subject.total_lessons }} zajęć
                                    </span>
                                    <span class="badge {% if subject.avg_score >= 70 %}badge-success{% else %}badge-ghost{% endif %}">
                                        {{ subject.avg_score }}/100
                                    </span>
                                </div>
                            </div>
                            {% widthratio subject.completed_lessons subject.total_lessons 100 as progress %}
                            <progress class="progress progress-primary w-full" value="{{ progress }}" max="100"></progress>
                        </div>
                    {% endfor %}
                </div>
            {% else %}
                <div class="text-center py-8 text-gray-500">
                    Brak danych o postępach
                </div>
            {% endif %}
        </div>
    </div>

    <!-- Achievements -->
    {% if achievements.badges %}
        <div class="card bg-base-100 shadow">
            <div class="card-body">
                <h2 class="card-title">Odznaki i osiągnięcia</h2>
                <p class="text-sm text-gray-600">Twoje odblokowane osiągnięcia</p>

                <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                    {% for badge in achievements.badges %}
                        <div class="border rounded-lg p-4 text-center {% if badge.unlocked %}bg-base-100{% else %}bg-base-200 opacity-50{% endif %}">
                            <div class="text-4xl mb-2">{{ badge.icon }}</div>
                            <div class="font-medium text-sm">{{ badge.name }}</div>
                            {% if badge.unlocked and badge.unlocked_at %}
                                <div class="text-xs text-gray-600 mt-1">
                                    {{ badge.unlocked_at|date:"j M Y" }}
                                </div>
                            {% endif %}
                        </div>
                    {% endfor %}
                </div>
            </div>
        </div>
    {% endif %}
</div>
{% endblock %}
```

---

## URL CONFIGURATION

**File**: `apps/students/urls.py`

```python
from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    # Dashboard
    path('', views.StudentDashboardView.as_view(), name='dashboard'),

    # Calendar
    path('calendar/', views.StudentCalendarView.as_view(), name='calendar'),
    path('calendar/events/', views.StudentCalendarEventsView.as_view(), name='calendar-events'),

    # Lessons
    path('lessons/<uuid:pk>/', views.StudentLessonDetailView.as_view(), name='lesson-detail'),

    # Cancellations
    path('cancellations/', views.CancellationRequestListView.as_view(), name='cancellation-list'),
    path('cancellations/create/', views.CancellationRequestCreateView.as_view(), name='cancellation-create'),

    # Makeup lessons
    path('makeup/', views.MakeupLessonsListView.as_view(), name='makeup-list'),
    path('makeup/<uuid:pk>/schedule/', views.MakeupScheduleView.as_view(), name='makeup-schedule'),

    # Progress
    path('progress/', views.StudentProgressView.as_view(), name='progress'),
]
```

---

## COMPLETION CHECKLIST

### Technical Validation

- [ ] Student dashboard operational
- [ ] Calendar displaying correctly
- [ ] Cancellation requests working
- [ ] Makeup tracker functional
- [ ] Progress view accurate
- [ ] All HTMX integrations successful

### Feature Validation

- [ ] Students can view their schedule
- [ ] Cancellation requests submittable
- [ ] 24h validation enforced
- [ ] Monthly limit enforced
- [ ] Makeup countdown accurate
- [ ] Progress stats calculated correctly
- [ ] Mobile responsive on all pages

### Integration Testing

- [ ] Django Views returning correct data
- [ ] Database queries optimized (select_related, prefetch_related)
- [ ] Form validation working
- [ ] Error handling comprehensive
- [ ] Permission checks in place (StudentRequiredMixin)

### Performance

- [ ] Dashboard loads quickly (<2s)
- [ ] Calendar renders smoothly
- [ ] No N+1 query issues
- [ ] Efficient data fetching

---

**Sprint Completion**: All 5 tasks completed and validated
**Next Sprint**: 9.3 - Parent Portal
