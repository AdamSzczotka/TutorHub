# Phase 5 - Sprint 5.2: Attendance Statistics & Reports (Django)

## Tasks 072-076: Attendance Analytics, Alerts & Reporting System

> **Duration**: Week 9 (Second half of Phase 5)
> **Goal**: Complete attendance reporting with statistics, alerts, and parent notifications
> **Dependencies**: Sprint 5.1 completed (Attendance Marking)

---

## SPRINT OVERVIEW

| Task ID | Description              | Priority | Dependencies |
| ------- | ------------------------ | -------- | ------------ |
| 072     | Attendance statistics    | Critical | Task 071     |
| 073     | Frequency alerts (<80%)  | High     | Task 072     |
| 074     | Monthly reports (PDF)    | High     | Task 073     |
| 075     | CSV export functionality | Medium   | Task 074     |
| 076     | Parent notifications     | High     | Task 075     |

---

## ATTENDANCE STATISTICS

### Statistics Service

**File**: `apps/attendance/services.py` (rozszerzenie)

```python
from django.db.models import Count, Q, F, Avg
from django.db.models.functions import TruncWeek, TruncMonth
from django.utils import timezone
from datetime import timedelta
from .models import AttendanceRecord


class AttendanceStatisticsService:
    """Service for calculating attendance statistics."""

    def get_student_statistics(self, student, start_date=None, end_date=None):
        """Calculate attendance statistics for a student."""
        queryset = AttendanceRecord.objects.filter(
            student=student
        ).select_related('lesson', 'lesson__subject')

        if start_date:
            queryset = queryset.filter(lesson__start_time__gte=start_date)
        if end_date:
            queryset = queryset.filter(lesson__start_time__lte=end_date)

        total = queryset.count()
        present = queryset.filter(status='PRESENT').count()
        late = queryset.filter(status='LATE').count()
        absent = queryset.filter(status='ABSENT').count()
        excused = queryset.filter(status='EXCUSED').count()

        attendance_rate = ((present + late) / total * 100) if total > 0 else 0

        return {
            'total': total,
            'present': present,
            'late': late,
            'absent': absent,
            'excused': excused,
            'attendance_rate': round(attendance_rate, 1),
        }

    def get_weekly_trend(self, student, weeks=8):
        """Get weekly attendance trend data."""
        end_date = timezone.now()
        start_date = end_date - timedelta(weeks=weeks)

        records = AttendanceRecord.objects.filter(
            student=student,
            lesson__start_time__gte=start_date,
            lesson__start_time__lte=end_date
        ).annotate(
            week=TruncWeek('lesson__start_time')
        ).values('week').annotate(
            total=Count('id'),
            present=Count('id', filter=Q(status='PRESENT')),
            late=Count('id', filter=Q(status='LATE')),
            absent=Count('id', filter=Q(status='ABSENT'))
        ).order_by('week')

        return [
            {
                'week': r['week'],
                'total': r['total'],
                'present': r['present'],
                'late': r['late'],
                'absent': r['absent'],
                'rate': round(
                    ((r['present'] + r['late']) / r['total'] * 100) if r['total'] > 0 else 0,
                    1
                )
            }
            for r in records
        ]

    def get_subject_breakdown(self, student, start_date=None, end_date=None):
        """Get attendance breakdown by subject."""
        queryset = AttendanceRecord.objects.filter(
            student=student
        ).select_related('lesson__subject')

        if start_date:
            queryset = queryset.filter(lesson__start_time__gte=start_date)
        if end_date:
            queryset = queryset.filter(lesson__start_time__lte=end_date)

        return queryset.values(
            'lesson__subject__name'
        ).annotate(
            total=Count('id'),
            present=Count('id', filter=Q(status='PRESENT')),
            late=Count('id', filter=Q(status='LATE')),
            absent=Count('id', filter=Q(status='ABSENT')),
            excused=Count('id', filter=Q(status='EXCUSED'))
        ).order_by('lesson__subject__name')

    def get_tutor_statistics(self, tutor, start_date=None, end_date=None):
        """Get attendance statistics for a tutor's lessons."""
        queryset = AttendanceRecord.objects.filter(
            lesson__tutor=tutor
        )

        if start_date:
            queryset = queryset.filter(lesson__start_time__gte=start_date)
        if end_date:
            queryset = queryset.filter(lesson__start_time__lte=end_date)

        total = queryset.count()
        present = queryset.filter(status='PRESENT').count()
        late = queryset.filter(status='LATE').count()
        absent = queryset.filter(status='ABSENT').count()

        return {
            'total': total,
            'present': present,
            'late': late,
            'absent': absent,
            'attendance_rate': round(
                ((present + late) / total * 100) if total > 0 else 0, 1
            )
        }

    def get_low_attendance_students(self, threshold=80, days=30):
        """Get students with attendance below threshold."""
        from apps.accounts.models import User

        cutoff_date = timezone.now() - timedelta(days=days)

        students = User.objects.filter(
            role='STUDENT',
            is_active=True
        ).prefetch_related('attendance_records')

        low_attendance = []

        for student in students:
            stats = self.get_student_statistics(
                student,
                start_date=cutoff_date
            )

            if stats['total'] > 0 and stats['attendance_rate'] < threshold:
                low_attendance.append({
                    'student': student,
                    'stats': stats
                })

        return sorted(
            low_attendance,
            key=lambda x: x['stats']['attendance_rate']
        )


statistics_service = AttendanceStatisticsService()
```

### Statistics Views

**File**: `apps/attendance/views.py` (rozszerzenie)

```python
from django.views.generic import TemplateView, View
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.core.mixins import AdminRequiredMixin, HTMXMixin
from .services import statistics_service
from datetime import datetime, timedelta


class StudentStatisticsView(LoginRequiredMixin, HTMXMixin, TemplateView):
    """Display attendance statistics for a student."""
    template_name = 'attendance/statistics/student_stats.html'
    partial_template_name = 'attendance/statistics/partials/_stats_content.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student_id = kwargs.get('student_id') or self.request.user.id

        # Date range from query params
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')

        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        else:
            start_date = datetime.now() - timedelta(days=90)

        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        else:
            end_date = datetime.now()

        from apps.accounts.models import User
        student = User.objects.get(id=student_id)

        context['student'] = student
        context['stats'] = statistics_service.get_student_statistics(
            student, start_date, end_date
        )
        context['weekly_trend'] = statistics_service.get_weekly_trend(student)
        context['subject_breakdown'] = statistics_service.get_subject_breakdown(
            student, start_date, end_date
        )
        context['start_date'] = start_date
        context['end_date'] = end_date

        return context


class AttendanceChartDataView(LoginRequiredMixin, View):
    """API endpoint for chart data (JSON)."""

    def get(self, request, student_id):
        from apps.accounts.models import User
        student = User.objects.get(id=student_id)

        weeks = int(request.GET.get('weeks', 8))
        trend_data = statistics_service.get_weekly_trend(student, weeks)

        return JsonResponse({
            'labels': [d['week'].strftime('%d %b') for d in trend_data],
            'rates': [d['rate'] for d in trend_data],
            'present': [d['present'] for d in trend_data],
            'absent': [d['absent'] for d in trend_data],
        })


class LowAttendanceListView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, TemplateView):
    """Display students with low attendance."""
    template_name = 'attendance/statistics/low_attendance.html'
    partial_template_name = 'attendance/statistics/partials/_low_attendance_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        threshold = int(self.request.GET.get('threshold', 80))
        days = int(self.request.GET.get('days', 30))

        context['students'] = statistics_service.get_low_attendance_students(
            threshold, days
        )
        context['threshold'] = threshold
        context['days'] = days

        return context
```

### Statistics Templates

**File**: `templates/attendance/statistics/student_stats.html`

```html
{% extends "base.html" %}

{% block content %}
<div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
        <div>
            <h1 class="text-2xl font-bold">Statystyki frekwencji</h1>
            <p class="text-base-content/70">{{ student.get_full_name }}</p>
        </div>

        <!-- Date Range Filter -->
        <div class="flex gap-2"
             x-data="{
                 startDate: '{{ start_date|date:'Y-m-d' }}',
                 endDate: '{{ end_date|date:'Y-m-d' }}'
             }">
            <input type="date"
                   class="input input-bordered input-sm"
                   x-model="startDate"
                   @change="htmx.ajax('GET', '?start_date=' + startDate + '&end_date=' + endDate, {target: '#stats-content', swap: 'innerHTML'})">
            <input type="date"
                   class="input input-bordered input-sm"
                   x-model="endDate"
                   @change="htmx.ajax('GET', '?start_date=' + startDate + '&end_date=' + endDate, {target: '#stats-content', swap: 'innerHTML'})">
        </div>
    </div>

    <div id="stats-content">
        {% include "attendance/statistics/partials/_stats_content.html" %}
    </div>
</div>
{% endblock %}
```

**File**: `templates/attendance/statistics/partials/_stats_content.html`

```html
<!-- Overview Cards -->
<div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
    <div class="stat bg-base-100 rounded-box shadow">
        <div class="stat-figure text-primary">
            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                      d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/>
            </svg>
        </div>
        <div class="stat-title">Wszystkie zajęcia</div>
        <div class="stat-value text-primary">{{ stats.total }}</div>
    </div>

    <div class="stat bg-base-100 rounded-box shadow">
        <div class="stat-figure {% if stats.attendance_rate >= 90 %}text-success{% elif stats.attendance_rate >= 80 %}text-warning{% else %}text-error{% endif %}">
            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                      d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
            </svg>
        </div>
        <div class="stat-title">Frekwencja</div>
        <div class="stat-value {% if stats.attendance_rate >= 90 %}text-success{% elif stats.attendance_rate >= 80 %}text-warning{% else %}text-error{% endif %}">
            {{ stats.attendance_rate }}%
        </div>
    </div>

    <div class="stat bg-base-100 rounded-box shadow">
        <div class="stat-figure text-success">
            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                      d="M5 13l4 4L19 7"/>
            </svg>
        </div>
        <div class="stat-title">Obecności</div>
        <div class="stat-value text-success">{{ stats.present }}</div>
        <div class="stat-desc">+ {{ stats.late }} spóźnień</div>
    </div>

    <div class="stat bg-base-100 rounded-box shadow">
        <div class="stat-figure text-error">
            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                      d="M6 18L18 6M6 6l12 12"/>
            </svg>
        </div>
        <div class="stat-title">Nieobecności</div>
        <div class="stat-value text-error">{{ stats.absent }}</div>
        <div class="stat-desc">+ {{ stats.excused }} usprawiedliwionych</div>
    </div>
</div>

<!-- Detailed Breakdown -->
<div class="card bg-base-100 shadow mb-6">
    <div class="card-body">
        <h2 class="card-title">
            Szczegółowe statystyki
            {% if stats.attendance_rate >= 80 %}
            <svg class="w-5 h-5 text-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                      d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/>
            </svg>
            {% else %}
            <svg class="w-5 h-5 text-error" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                      d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6"/>
            </svg>
            {% endif %}
        </h2>
        <p class="text-base-content/70">Rozkład obecności według statusu</p>

        <div class="space-y-4 mt-4">
            <!-- Present -->
            <div class="space-y-2">
                <div class="flex items-center justify-between">
                    <div class="flex items-center gap-2">
                        <div class="w-3 h-3 rounded-full bg-success"></div>
                        <span class="text-sm font-medium">Obecny</span>
                    </div>
                    <span class="text-sm text-base-content/70">
                        {{ stats.present }} ({% widthratio stats.present stats.total 100 %}%)
                    </span>
                </div>
                <progress class="progress progress-success w-full"
                          value="{{ stats.present }}"
                          max="{{ stats.total }}"></progress>
            </div>

            <!-- Late -->
            <div class="space-y-2">
                <div class="flex items-center justify-between">
                    <div class="flex items-center gap-2">
                        <div class="w-3 h-3 rounded-full bg-warning"></div>
                        <span class="text-sm font-medium">Spóźniony</span>
                    </div>
                    <span class="text-sm text-base-content/70">
                        {{ stats.late }} ({% widthratio stats.late stats.total 100 %}%)
                    </span>
                </div>
                <progress class="progress progress-warning w-full"
                          value="{{ stats.late }}"
                          max="{{ stats.total }}"></progress>
            </div>

            <!-- Absent -->
            <div class="space-y-2">
                <div class="flex items-center justify-between">
                    <div class="flex items-center gap-2">
                        <div class="w-3 h-3 rounded-full bg-error"></div>
                        <span class="text-sm font-medium">Nieobecny</span>
                    </div>
                    <span class="text-sm text-base-content/70">
                        {{ stats.absent }} ({% widthratio stats.absent stats.total 100 %}%)
                    </span>
                </div>
                <progress class="progress progress-error w-full"
                          value="{{ stats.absent }}"
                          max="{{ stats.total }}"></progress>
            </div>

            <!-- Excused -->
            <div class="space-y-2">
                <div class="flex items-center justify-between">
                    <div class="flex items-center gap-2">
                        <div class="w-3 h-3 rounded-full bg-info"></div>
                        <span class="text-sm font-medium">Usprawiedliwiony</span>
                    </div>
                    <span class="text-sm text-base-content/70">
                        {{ stats.excused }} ({% widthratio stats.excused stats.total 100 %}%)
                    </span>
                </div>
                <progress class="progress progress-info w-full"
                          value="{{ stats.excused }}"
                          max="{{ stats.total }}"></progress>
            </div>
        </div>

        {% if stats.attendance_rate < 80 %}
        <div class="alert alert-error mt-4">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                      d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
            </svg>
            <div>
                <h3 class="font-bold">Niska frekwencja</h3>
                <p class="text-sm">Frekwencja poniżej 80% wymaga uwagi. Skontaktuj się z rodzicem.</p>
            </div>
        </div>
        {% endif %}
    </div>
</div>

<!-- Weekly Trend Chart -->
<div class="card bg-base-100 shadow">
    <div class="card-body">
        <h2 class="card-title">Trend frekwencji</h2>
        <p class="text-base-content/70">Wykres tygodniowy obecności</p>

        <div class="h-64 flex items-end justify-between gap-2 mt-4"
             x-data="{ data: {{ weekly_trend|safe }} }">
            <template x-for="(week, index) in data" :key="index">
                <div class="flex-1 flex flex-col items-center gap-2">
                    <div class="text-xs font-medium" x-text="week.rate + '%'"></div>
                    <div class="w-full rounded-t transition-all hover:opacity-80"
                         :class="{
                             'bg-success': week.rate >= 90,
                             'bg-warning': week.rate >= 80 && week.rate < 90,
                             'bg-error': week.rate < 80
                         }"
                         :style="'height: ' + (week.rate) + '%'"
                         :title="week.week"></div>
                    <div class="text-xs text-base-content/70 -rotate-45 origin-top-left mt-2"
                         x-text="new Date(week.week).toLocaleDateString('pl-PL', {day: '2-digit', month: 'short'})">
                    </div>
                </div>
            </template>
        </div>

        <div x-show="data.length === 0" class="flex items-center justify-center h-64 text-base-content/50">
            Brak danych do wyświetlenia
        </div>
    </div>
</div>
```

---

## FREQUENCY ALERTS

### Alert Service

**File**: `apps/attendance/services.py` (rozszerzenie)

```python
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from .models import AttendanceAlert


class AttendanceAlertService:
    """Service for managing attendance alerts."""

    DEFAULT_THRESHOLD = 80

    def check_and_create_alerts(self, threshold=None):
        """Check all students and create alerts for low attendance."""
        threshold = threshold or self.DEFAULT_THRESHOLD

        low_attendance = statistics_service.get_low_attendance_students(threshold)
        alerts = []

        for item in low_attendance:
            student = item['student']
            stats = item['stats']

            # Check if alert already exists for this period
            existing = AttendanceAlert.objects.filter(
                student=student,
                status='PENDING',
                threshold=threshold
            ).exists()

            if existing:
                continue

            # Create alert
            alert = AttendanceAlert.objects.create(
                student=student,
                attendance_rate=stats['attendance_rate'],
                threshold=threshold,
                alert_type='LOW_ATTENDANCE',
                status='PENDING'
            )

            # Send notifications
            self._send_admin_alert(student, stats, threshold)

            if hasattr(student, 'student_profile') and student.student_profile.parent_email:
                self._send_parent_alert(student, stats, threshold)

            alerts.append(alert)

        return alerts

    def _send_admin_alert(self, student, stats, threshold):
        """Send alert email to admins."""
        from apps.accounts.models import User

        admins = User.objects.filter(role='ADMIN', is_active=True)

        for admin in admins:
            context = {
                'admin_name': admin.get_full_name(),
                'student_name': student.get_full_name(),
                'student_class': getattr(student.student_profile, 'class_name', 'N/A'),
                'attendance_rate': stats['attendance_rate'],
                'threshold': threshold,
                'total_lessons': stats['total'],
                'present_count': stats['present'],
                'absent_count': stats['absent'],
                'late_count': stats['late'],
            }

            html_content = render_to_string(
                'emails/low_attendance_admin.html',
                context
            )

            send_mail(
                subject=f"Alert: Niska frekwencja - {student.get_full_name()}",
                message='',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[admin.email],
                html_message=html_content
            )

    def _send_parent_alert(self, student, stats, threshold):
        """Send alert email to parent."""
        profile = student.student_profile

        if not profile.parent_email:
            return

        context = {
            'parent_name': profile.parent_name or 'Szanowni Państwo',
            'student_name': student.get_full_name(),
            'attendance_rate': stats['attendance_rate'],
            'threshold': threshold,
            'total_lessons': stats['total'],
            'present_count': stats['present'],
            'absent_count': stats['absent'],
            'recommendation': 'Prosimy o kontakt z administratorem w celu omówienia sytuacji.'
        }

        html_content = render_to_string(
            'emails/low_attendance_parent.html',
            context
        )

        send_mail(
            subject=f"Powiadomienie o frekwencji - {student.get_full_name()}",
            message='',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[profile.parent_email],
            html_message=html_content
        )

    def get_active_alerts(self):
        """Get all pending alerts."""
        return AttendanceAlert.objects.filter(
            status='PENDING'
        ).select_related(
            'student',
            'student__student_profile'
        ).order_by('-created_at')

    def resolve_alert(self, alert_id, resolution):
        """Mark alert as resolved."""
        alert = AttendanceAlert.objects.get(id=alert_id)
        alert.status = 'RESOLVED'
        alert.resolution = resolution
        alert.resolved_at = timezone.now()
        alert.save()
        return alert

    def dismiss_alert(self, alert_id):
        """Dismiss an alert."""
        alert = AttendanceAlert.objects.get(id=alert_id)
        alert.status = 'DISMISSED'
        alert.resolved_at = timezone.now()
        alert.save()
        return alert


alert_service = AttendanceAlertService()
```

### Alert Views

**File**: `apps/attendance/views.py` (rozszerzenie)

```python
class AttendanceAlertListView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, TemplateView):
    """Display active attendance alerts."""
    template_name = 'attendance/alerts/list.html'
    partial_template_name = 'attendance/alerts/partials/_alert_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['alerts'] = alert_service.get_active_alerts()
        return context


class ResolveAlertView(LoginRequiredMixin, AdminRequiredMixin, View):
    """Resolve an attendance alert."""

    def post(self, request, alert_id):
        resolution = request.POST.get('resolution', '')

        if not resolution.strip():
            return HttpResponse(
                '<div class="alert alert-error">Opis rozwiązania jest wymagany.</div>',
                status=400
            )

        alert_service.resolve_alert(alert_id, resolution)

        return HttpResponse(
            status=204,
            headers={'HX-Trigger': 'alertResolved'}
        )


class DismissAlertView(LoginRequiredMixin, AdminRequiredMixin, View):
    """Dismiss an attendance alert."""

    def post(self, request, alert_id):
        alert_service.dismiss_alert(alert_id)

        return HttpResponse(
            status=204,
            headers={'HX-Trigger': 'alertDismissed'}
        )
```

### Alert Templates

**File**: `templates/attendance/alerts/list.html`

```html
{% extends "admin_panel/base.html" %}

{% block content %}
<div class="space-y-6">
    <div class="flex items-center justify-between">
        <div>
            <h1 class="text-2xl font-bold">Alerty frekwencji</h1>
            <p class="text-base-content/70">Uczniowie z frekwencją poniżej progu</p>
        </div>

        <button class="btn btn-primary"
                hx-post="{% url 'attendance:check_alerts' %}"
                hx-target="#alert-list"
                hx-swap="innerHTML">
            <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                      d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
            </svg>
            Sprawdź teraz
        </button>
    </div>

    <div id="alert-list"
         hx-get="{% url 'attendance:alerts' %}"
         hx-trigger="alertResolved from:body, alertDismissed from:body"
         hx-swap="innerHTML">
        {% include "attendance/alerts/partials/_alert_list.html" %}
    </div>
</div>

<!-- Resolution Modal -->
<dialog id="resolve-modal" class="modal">
    <div class="modal-box">
        <h3 class="font-bold text-lg">Rozwiąż alert frekwencji</h3>
        <div id="resolve-modal-content"></div>
    </div>
    <form method="dialog" class="modal-backdrop">
        <button>close</button>
    </form>
</dialog>
{% endblock %}
```

**File**: `templates/attendance/alerts/partials/_alert_list.html`

```html
{% if alerts %}
<div class="space-y-3">
    {% for alert in alerts %}
    <div class="flex items-center justify-between p-4 bg-warning/10 border border-warning/30 rounded-lg">
        <div class="flex-1">
            <div class="font-medium">
                {{ alert.student.get_full_name }}
            </div>
            <div class="text-sm text-base-content/70">
                Klasa: {{ alert.student.student_profile.class_name|default:"N/A" }} •
                Frekwencja: <strong class="text-error">{{ alert.attendance_rate }}%</strong>
            </div>
            <div class="text-xs text-base-content/50 mt-1">
                Utworzono: {{ alert.created_at|date:"d.m.Y H:i" }}
            </div>
        </div>

        <div class="flex items-center gap-2">
            <span class="badge badge-error gap-1">
                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                          d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
                </svg>
                &lt;{{ alert.threshold }}%
            </span>

            <button class="btn btn-sm btn-outline"
                    hx-get="{% url 'attendance:resolve_alert_form' alert.id %}"
                    hx-target="#resolve-modal-content"
                    onclick="document.getElementById('resolve-modal').showModal()">
                Rozwiąż
            </button>

            <button class="btn btn-sm btn-ghost"
                    hx-post="{% url 'attendance:dismiss_alert' alert.id %}"
                    hx-confirm="Czy na pewno chcesz odrzucić ten alert?">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                          d="M6 18L18 6M6 6l12 12"/>
                </svg>
            </button>
        </div>
    </div>
    {% endfor %}
</div>
{% else %}
<div class="flex items-center justify-center h-24 text-base-content/50">
    <svg class="w-5 h-5 mr-2 text-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
    </svg>
    Brak alertów o niskiej frekwencji
</div>
{% endif %}
```

**File**: `templates/attendance/alerts/partials/_resolve_form.html`

```html
<form hx-post="{% url 'attendance:resolve_alert' alert.id %}"
      hx-target="#alert-list"
      hx-swap="innerHTML"
      class="space-y-4">
    {% csrf_token %}

    <div class="text-sm text-base-content/70">
        Uczeń: <strong>{{ alert.student.get_full_name }}</strong><br>
        Frekwencja: <strong class="text-error">{{ alert.attendance_rate }}%</strong>
    </div>

    <div class="form-control">
        <label class="label">
            <span class="label-text">Opis rozwiązania *</span>
        </label>
        <textarea name="resolution"
                  class="textarea textarea-bordered w-full"
                  rows="4"
                  placeholder="Opisz podjęte działania lub rozwiązanie problemu..."
                  required></textarea>
    </div>

    <div class="modal-action">
        <button type="button"
                class="btn btn-ghost"
                onclick="document.getElementById('resolve-modal').close()">
            Anuluj
        </button>
        <button type="submit" class="btn btn-primary">
            Rozwiąż
        </button>
    </div>
</form>
```

### Celery Task for Alerts

**File**: `apps/attendance/tasks.py` (rozszerzenie)

```python
from celery import shared_task


@shared_task
def check_attendance_alerts():
    """Periodic task to check and send attendance alerts."""
    from .services import alert_service
    alerts = alert_service.check_and_create_alerts()
    return f"Created {len(alerts)} new alerts"


# Add to celery beat schedule in settings:
# CELERY_BEAT_SCHEDULE = {
#     'check-attendance-alerts': {
#         'task': 'apps.attendance.tasks.check_attendance_alerts',
#         'schedule': crontab(hour=8, minute=0),  # Every day at 8:00 AM
#     },
# }
```

---

## MONTHLY REPORTS (PDF)

### Report Service with WeasyPrint

**File**: `apps/attendance/services.py` (rozszerzenie)

```python
from django.template.loader import render_to_string
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
from io import BytesIO
import os


class AttendanceReportService:
    """Service for generating attendance reports."""

    def generate_monthly_report(self, student, month):
        """Generate monthly attendance report PDF for a student."""
        from datetime import datetime
        from django.utils import timezone

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
        records = AttendanceRecord.objects.filter(
            student=student,
            lesson__start_time__gte=start_date,
            lesson__start_time__lt=end_date
        ).select_related(
            'lesson',
            'lesson__subject',
            'lesson__tutor'
        ).order_by('lesson__start_time')

        # Calculate statistics
        stats = statistics_service.get_student_statistics(
            student, start_date, end_date
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
        html_content = render_to_string(
            'reports/attendance_monthly.html',
            context
        )

        # Generate PDF
        font_config = FontConfiguration()
        css = CSS(string='''
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
        ''', font_config=font_config)

        html = HTML(string=html_content)
        pdf_buffer = BytesIO()
        html.write_pdf(pdf_buffer, stylesheets=[css], font_config=font_config)
        pdf_buffer.seek(0)

        # Save report record
        from .models import AttendanceReport
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
            }
        )

        return report, pdf_buffer

    def generate_and_send_monthly_reports(self, month):
        """Generate and email monthly reports for all students."""
        from apps.accounts.models import User

        students = User.objects.filter(
            role='STUDENT',
            is_active=True
        ).select_related('student_profile')

        results = []

        for student in students:
            try:
                report, pdf_buffer = self.generate_monthly_report(student, month)

                # Send to parent if email available
                profile = getattr(student, 'student_profile', None)
                if profile and profile.parent_email:
                    self._send_report_email(student, report, pdf_buffer, month)

                results.append({
                    'student': student,
                    'report': report,
                    'success': True
                })
            except Exception as e:
                results.append({
                    'student': student,
                    'success': False,
                    'error': str(e)
                })

        return results

    def _send_report_email(self, student, report, pdf_buffer, month):
        """Send monthly report email to parent."""
        from django.core.mail import EmailMessage

        profile = student.student_profile

        context = {
            'parent_name': profile.parent_name or 'Szanowni Państwo',
            'student_name': student.get_full_name(),
            'month': month.strftime('%B %Y'),
            'attendance_rate': report.attendance_rate,
        }

        html_content = render_to_string(
            'emails/monthly_attendance_report.html',
            context
        )

        email = EmailMessage(
            subject=f"Raport frekwencji - {month.strftime('%B %Y')}",
            body=html_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[profile.parent_email]
        )
        email.content_subtype = 'html'

        # Attach PDF
        email.attach(
            f"raport-frekwencji-{month.strftime('%Y-%m')}.pdf",
            pdf_buffer.getvalue(),
            'application/pdf'
        )

        email.send()


report_service = AttendanceReportService()
```

### Report HTML Template

**File**: `templates/reports/attendance_monthly.html`

```html
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <title>Raport frekwencji - {{ month_name }}</title>
</head>
<body>
    <!-- Header -->
    <div class="header">
        <div class="title">Raport frekwencji</div>
        <div class="subtitle">
            Okres: {{ month_name }} • Wygenerowano: {{ generated_at|date:"d.m.Y H:i" }}
        </div>
    </div>

    <!-- Student Info -->
    <div style="margin-bottom: 20px; padding: 15px; background-color: #F3F4F6; border-radius: 5px;">
        <div style="margin-bottom: 5px;">
            <strong>Uczeń:</strong> {{ student.get_full_name }}
        </div>
        <div style="margin-bottom: 5px;">
            <strong>Klasa:</strong> {{ student.student_profile.class_name|default:"N/A" }}
        </div>
        <div>
            <strong>Email:</strong> {{ student.email }}
        </div>
    </div>

    <!-- Statistics -->
    <div class="stats-grid">
        <div class="stat-box">
            <div class="stat-value" style="color: #3B82F6;">{{ statistics.total }}</div>
            <div class="stat-label">Zajęcia</div>
        </div>
        <div class="stat-box">
            <div class="stat-value" style="color: {% if statistics.attendance_rate >= 90 %}#10B981{% elif statistics.attendance_rate >= 80 %}#F59E0B{% else %}#EF4444{% endif %};">
                {{ statistics.attendance_rate }}%
            </div>
            <div class="stat-label">Frekwencja</div>
        </div>
        <div class="stat-box">
            <div class="stat-value" style="color: #10B981;">{{ statistics.present }}</div>
            <div class="stat-label">Obecności</div>
        </div>
        <div class="stat-box">
            <div class="stat-value" style="color: #EF4444;">{{ statistics.absent }}</div>
            <div class="stat-label">Nieobecności</div>
        </div>
    </div>

    <!-- Attendance Table -->
    <table>
        <thead>
            <tr>
                <th style="width: 15%;">Data</th>
                <th style="width: 10%;">Godzina</th>
                <th style="width: 25%;">Przedmiot</th>
                <th style="width: 20%;">Korepetytor</th>
                <th style="width: 15%;">Status</th>
                <th style="width: 15%;">Notatki</th>
            </tr>
        </thead>
        <tbody>
            {% for record in records %}
            <tr>
                <td>{{ record.lesson.start_time|date:"d.m.Y" }}</td>
                <td>{{ record.lesson.start_time|time:"H:i" }}</td>
                <td>{{ record.lesson.subject.name }}</td>
                <td>{{ record.lesson.tutor.get_full_name }}</td>
                <td class="status-{{ record.status|lower }}">
                    {% if record.status == 'PRESENT' %}Obecny
                    {% elif record.status == 'LATE' %}Spóźniony
                    {% elif record.status == 'ABSENT' %}Nieobecny
                    {% elif record.status == 'EXCUSED' %}Usprawiedliwiony
                    {% else %}Oczekujące{% endif %}
                </td>
                <td>{{ record.notes|default:"-" }}</td>
            </tr>
            {% empty %}
            <tr>
                <td colspan="6" style="text-align: center; color: #6B7280;">
                    Brak zapisów obecności w tym miesiącu
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

    <!-- Footer -->
    <div class="footer">
        System zarządzania szkołą korepetycji "Na Piątkę" • Raport wygenerowany automatycznie
    </div>
</body>
</html>
```

### Report Views

**File**: `apps/attendance/views.py` (rozszerzenie)

```python
from django.http import FileResponse


class GenerateReportView(LoginRequiredMixin, View):
    """Generate and download attendance report PDF."""

    def get(self, request, student_id):
        from apps.accounts.models import User
        from datetime import datetime

        student = User.objects.get(id=student_id)

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

        filename = f"raport-frekwencji-{student.get_full_name().replace(' ', '-')}-{month.strftime('%Y-%m')}.pdf"

        return FileResponse(
            pdf_buffer,
            as_attachment=True,
            filename=filename,
            content_type='application/pdf'
        )


class BulkGenerateReportsView(LoginRequiredMixin, AdminRequiredMixin, View):
    """Generate monthly reports for all students."""

    def post(self, request):
        from datetime import datetime

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
            '<div class="alert alert-success">Generowanie raportów zostało zaplanowane. Raporty zostaną wysłane emailem.</div>'
        )
```

### Celery Task for Reports

**File**: `apps/attendance/tasks.py` (rozszerzenie)

```python
@shared_task
def generate_monthly_reports_task(month_str):
    """Background task to generate and send monthly reports."""
    from datetime import datetime
    from .services import report_service

    month = datetime.fromisoformat(month_str)
    results = report_service.generate_and_send_monthly_reports(month)

    success_count = sum(1 for r in results if r['success'])
    return f"Generated {success_count}/{len(results)} reports for {month.strftime('%B %Y')}"


# Add to celery beat schedule:
# CELERY_BEAT_SCHEDULE = {
#     'generate-monthly-reports': {
#         'task': 'apps.attendance.tasks.generate_monthly_reports_task',
#         'schedule': crontab(day_of_month=1, hour=6, minute=0),  # First day of month at 6:00 AM
#     },
# }
```

---

## CSV EXPORT

### Export Service

**File**: `apps/attendance/services.py` (rozszerzenie)

```python
import csv
from io import StringIO


class AttendanceExportService:
    """Service for exporting attendance data."""

    STATUS_LABELS = {
        'PRESENT': 'Obecny',
        'LATE': 'Spóźniony',
        'ABSENT': 'Nieobecny',
        'EXCUSED': 'Usprawiedliwiony',
        'PENDING': 'Oczekujące',
    }

    def export_to_csv(self, start_date, end_date, student_id=None, subject_id=None):
        """Export attendance records to CSV."""
        queryset = AttendanceRecord.objects.filter(
            lesson__start_time__gte=start_date,
            lesson__start_time__lte=end_date
        ).select_related(
            'student',
            'student__student_profile',
            'lesson',
            'lesson__subject',
            'lesson__tutor'
        ).order_by('-lesson__start_time')

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
        writer.writerow([
            'Data',
            'Godzina',
            'Uczeń',
            'Klasa',
            'Przedmiot',
            'Korepetytor',
            'Status',
            'Notatki'
        ])

        # Data rows
        for record in queryset:
            profile = getattr(record.student, 'student_profile', None)
            writer.writerow([
                record.lesson.start_time.strftime('%d.%m.%Y'),
                record.lesson.start_time.strftime('%H:%M'),
                record.student.get_full_name(),
                profile.class_name if profile else 'N/A',
                record.lesson.subject.name,
                record.lesson.tutor.get_full_name(),
                self.STATUS_LABELS.get(record.status, record.status),
                record.notes or ''
            ])

        return output.getvalue()


export_service = AttendanceExportService()
```

### Export Views

**File**: `apps/attendance/views.py` (rozszerzenie)

```python
from django.http import HttpResponse as DjangoHttpResponse


class ExportCSVView(LoginRequiredMixin, AdminRequiredMixin, View):
    """Export attendance data to CSV."""

    def get(self, request):
        from datetime import datetime, timedelta

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
            subject_id
        )

        filename = f"frekwencja-{start_date.strftime('%Y-%m-%d')}-{end_date.strftime('%Y-%m-%d')}.csv"

        response = DjangoHttpResponse(
            csv_content,
            content_type='text/csv; charset=utf-8'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        return response
```

### Export Modal Template

**File**: `templates/attendance/partials/_export_modal.html`

```html
<div x-data="{
    startDate: new Date(Date.now() - 30*24*60*60*1000).toISOString().split('T')[0],
    endDate: new Date().toISOString().split('T')[0],
    studentId: '',
    subjectId: ''
}">
    <h3 class="font-bold text-lg mb-4">Eksport frekwencji do CSV</h3>
    <p class="text-base-content/70 mb-4">Wybierz zakres dat dla eksportu danych</p>

    <div class="space-y-4">
        <div class="form-control">
            <label class="label">
                <span class="label-text">Data rozpoczęcia</span>
            </label>
            <input type="date"
                   class="input input-bordered w-full"
                   x-model="startDate">
        </div>

        <div class="form-control">
            <label class="label">
                <span class="label-text">Data zakończenia</span>
            </label>
            <input type="date"
                   class="input input-bordered w-full"
                   x-model="endDate">
        </div>

        <div class="form-control">
            <label class="label">
                <span class="label-text">Uczeń (opcjonalnie)</span>
            </label>
            <select class="select select-bordered w-full" x-model="studentId">
                <option value="">Wszyscy uczniowie</option>
                {% for student in students %}
                <option value="{{ student.id }}">{{ student.get_full_name }}</option>
                {% endfor %}
            </select>
        </div>

        <div class="form-control">
            <label class="label">
                <span class="label-text">Przedmiot (opcjonalnie)</span>
            </label>
            <select class="select select-bordered w-full" x-model="subjectId">
                <option value="">Wszystkie przedmioty</option>
                {% for subject in subjects %}
                <option value="{{ subject.id }}">{{ subject.name }}</option>
                {% endfor %}
            </select>
        </div>
    </div>

    <div class="modal-action">
        <button class="btn btn-ghost" onclick="document.getElementById('export-modal').close()">
            Anuluj
        </button>
        <a class="btn btn-primary"
           :href="`{% url 'attendance:export_csv' %}?start_date=${startDate}&end_date=${endDate}&student_id=${studentId}&subject_id=${subjectId}`"
           download>
            <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                      d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
            </svg>
            Eksportuj
        </a>
    </div>
</div>
```

---

## PARENT NOTIFICATIONS

### Parent Notification Service

**File**: `apps/notifications/services.py`

```python
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import secrets


class ParentNotificationService:
    """Service for parent notifications."""

    def send_absence_alert(self, student, lesson):
        """Send immediate absence alert to parent."""
        profile = getattr(student, 'student_profile', None)

        if not profile or not profile.parent_email:
            return False

        context = {
            'parent_name': profile.parent_name or 'Szanowni Państwo',
            'student_name': student.get_full_name(),
            'lesson_title': lesson.title,
            'lesson_date': lesson.start_time.strftime('%d %B %Y'),
            'lesson_time': lesson.start_time.strftime('%H:%M'),
            'subject': lesson.subject.name,
            'tutor': lesson.tutor.get_full_name(),
        }

        html_content = render_to_string(
            'emails/absence_alert.html',
            context
        )

        send_mail(
            subject=f"Alert: Nieobecność - {student.get_full_name()}",
            message='',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[profile.parent_email],
            html_message=html_content
        )

        return True

    def send_weekly_summaries(self):
        """Send weekly attendance summaries to all parents."""
        from apps.accounts.models import User
        from apps.attendance.models import AttendanceRecord

        week_start = timezone.now() - timedelta(days=7)
        week_end = timezone.now()

        students = User.objects.filter(
            role='STUDENT',
            is_active=True,
            student_profile__parent_email__isnull=False
        ).exclude(
            student_profile__parent_email=''
        ).select_related('student_profile')

        sent_count = 0

        for student in students:
            profile = student.student_profile

            # Get week's attendance
            records = AttendanceRecord.objects.filter(
                student=student,
                lesson__start_time__gte=week_start,
                lesson__start_time__lte=week_end
            ).select_related('lesson', 'lesson__subject')

            if not records.exists():
                continue

            total = records.count()
            present = records.filter(status='PRESENT').count()
            late = records.filter(status='LATE').count()
            absent = records.filter(status='ABSENT').count()
            rate = round(((present + late) / total * 100), 1) if total > 0 else 0

            context = {
                'parent_name': profile.parent_name or 'Szanowni Państwo',
                'student_name': student.get_full_name(),
                'week_start': week_start.strftime('%d %b'),
                'week_end': week_end.strftime('%d %b %Y'),
                'total_lessons': total,
                'present_count': present,
                'late_count': late,
                'absent_count': absent,
                'attendance_rate': rate,
                'lessons': [
                    {
                        'date': r.lesson.start_time.strftime('%d.%m.%Y'),
                        'subject': r.lesson.subject.name,
                        'status': self._get_status_label(r.status)
                    }
                    for r in records.order_by('lesson__start_time')
                ]
            }

            html_content = render_to_string(
                'emails/weekly_summary.html',
                context
            )

            send_mail(
                subject=f"Podsumowanie tygodnia - {student.get_full_name()}",
                message='',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[profile.parent_email],
                html_message=html_content
            )

            sent_count += 1

        return sent_count

    def grant_portal_access(self, student, parent_email):
        """Grant parent portal access."""
        profile = student.student_profile

        # Generate access token
        access_token = secrets.token_urlsafe(32)

        # Update profile
        profile.parent_email = parent_email
        profile.parent_portal_token = access_token
        profile.parent_portal_enabled = True
        profile.save()

        # Send access email
        context = {
            'parent_name': profile.parent_name or 'Szanowni Państwo',
            'student_name': student.get_full_name(),
            'access_link': f"{settings.SITE_URL}/parent-portal/?token={access_token}",
            'instructions': 'Kliknij w link powyżej, aby uzyskać dostęp do portalu rodzica.'
        }

        html_content = render_to_string(
            'emails/parent_portal_access.html',
            context
        )

        send_mail(
            subject=f"Dostęp do portalu rodzica - {student.get_full_name()}",
            message='',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[parent_email],
            html_message=html_content
        )

        return access_token

    def _get_status_label(self, status):
        """Get Polish label for status."""
        labels = {
            'PRESENT': 'Obecny',
            'LATE': 'Spóźniony',
            'ABSENT': 'Nieobecny',
            'EXCUSED': 'Usprawiedliwiony',
        }
        return labels.get(status, 'Oczekujące')


parent_notification_service = ParentNotificationService()
```

### Celery Tasks for Notifications

**File**: `apps/notifications/tasks.py`

```python
from celery import shared_task


@shared_task
def send_absence_alert_task(student_id, lesson_id):
    """Send absence alert to parent."""
    from apps.accounts.models import User
    from apps.lessons.models import Lesson
    from .services import parent_notification_service

    student = User.objects.get(id=student_id)
    lesson = Lesson.objects.get(id=lesson_id)

    return parent_notification_service.send_absence_alert(student, lesson)


@shared_task
def send_weekly_summaries_task():
    """Weekly task to send attendance summaries to parents."""
    from .services import parent_notification_service

    sent = parent_notification_service.send_weekly_summaries()
    return f"Sent {sent} weekly summaries"


# Celery beat schedule:
# CELERY_BEAT_SCHEDULE = {
#     'send-weekly-summaries': {
#         'task': 'apps.notifications.tasks.send_weekly_summaries_task',
#         'schedule': crontab(day_of_week=0, hour=18, minute=0),  # Sunday at 6 PM
#     },
# }
```

### Email Templates

**File**: `templates/emails/absence_alert.html`

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: #EF4444; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
            <h1 style="margin: 0; font-size: 24px;">Alert: Nieobecność</h1>
        </div>

        <div style="background: #fff; padding: 20px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 8px 8px;">
            <p>{{ parent_name }},</p>

            <p>Informujemy, że <strong>{{ student_name }}</strong> był/a nieobecny/a na zajęciach:</p>

            <div style="background: #f9fafb; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <p style="margin: 5px 0;"><strong>Przedmiot:</strong> {{ subject }}</p>
                <p style="margin: 5px 0;"><strong>Data:</strong> {{ lesson_date }}</p>
                <p style="margin: 5px 0;"><strong>Godzina:</strong> {{ lesson_time }}</p>
                <p style="margin: 5px 0;"><strong>Korepetytor:</strong> {{ tutor }}</p>
            </div>

            <p>Prosimy o kontakt w celu wyjaśnienia nieobecności.</p>

            <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
                Pozdrawiamy,<br>
                Zespół "Na Piątkę"
            </p>
        </div>
    </div>
</body>
</html>
```

**File**: `templates/emails/weekly_summary.html`

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: #3B82F6; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
            <h1 style="margin: 0; font-size: 24px;">Podsumowanie tygodnia</h1>
            <p style="margin: 5px 0 0 0; opacity: 0.9;">{{ week_start }} - {{ week_end }}</p>
        </div>

        <div style="background: #fff; padding: 20px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 8px 8px;">
            <p>{{ parent_name }},</p>

            <p>Oto podsumowanie frekwencji ucznia <strong>{{ student_name }}</strong> w mijającym tygodniu:</p>

            <!-- Statistics -->
            <div style="display: flex; gap: 10px; margin: 20px 0; text-align: center;">
                <div style="flex: 1; background: #f9fafb; padding: 15px; border-radius: 8px;">
                    <div style="font-size: 28px; font-weight: bold; color: #3B82F6;">{{ total_lessons }}</div>
                    <div style="font-size: 12px; color: #6b7280;">Zajęcia</div>
                </div>
                <div style="flex: 1; background: #f9fafb; padding: 15px; border-radius: 8px;">
                    <div style="font-size: 28px; font-weight: bold; color: {% if attendance_rate >= 80 %}#10B981{% else %}#EF4444{% endif %};">
                        {{ attendance_rate }}%
                    </div>
                    <div style="font-size: 12px; color: #6b7280;">Frekwencja</div>
                </div>
                <div style="flex: 1; background: #f9fafb; padding: 15px; border-radius: 8px;">
                    <div style="font-size: 28px; font-weight: bold; color: #10B981;">{{ present_count }}</div>
                    <div style="font-size: 12px; color: #6b7280;">Obecności</div>
                </div>
                <div style="flex: 1; background: #f9fafb; padding: 15px; border-radius: 8px;">
                    <div style="font-size: 28px; font-weight: bold; color: #EF4444;">{{ absent_count }}</div>
                    <div style="font-size: 12px; color: #6b7280;">Nieobecności</div>
                </div>
            </div>

            <!-- Lessons table -->
            <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
                <thead>
                    <tr style="background: #f3f4f6;">
                        <th style="padding: 10px; text-align: left; border-bottom: 1px solid #e5e7eb;">Data</th>
                        <th style="padding: 10px; text-align: left; border-bottom: 1px solid #e5e7eb;">Przedmiot</th>
                        <th style="padding: 10px; text-align: left; border-bottom: 1px solid #e5e7eb;">Status</th>
                    </tr>
                </thead>
                <tbody>
                    {% for lesson in lessons %}
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #e5e7eb;">{{ lesson.date }}</td>
                        <td style="padding: 10px; border-bottom: 1px solid #e5e7eb;">{{ lesson.subject }}</td>
                        <td style="padding: 10px; border-bottom: 1px solid #e5e7eb;">
                            <span style="color: {% if lesson.status == 'Obecny' %}#10B981{% elif lesson.status == 'Spóźniony' %}#F59E0B{% elif lesson.status == 'Nieobecny' %}#EF4444{% else %}#3B82F6{% endif %};">
                                {{ lesson.status }}
                            </span>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>

            <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
                Pozdrawiamy,<br>
                Zespół "Na Piątkę"
            </p>
        </div>
    </div>
</body>
</html>
```

---

## URL CONFIGURATION

**File**: `apps/attendance/urls.py` (rozszerzenie)

```python
from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    # ... existing urls ...

    # Statistics
    path('statistics/', views.StudentStatisticsView.as_view(), name='statistics'),
    path('statistics/<uuid:student_id>/', views.StudentStatisticsView.as_view(), name='student_statistics'),
    path('statistics/<uuid:student_id>/chart/', views.AttendanceChartDataView.as_view(), name='chart_data'),
    path('low-attendance/', views.LowAttendanceListView.as_view(), name='low_attendance'),

    # Alerts
    path('alerts/', views.AttendanceAlertListView.as_view(), name='alerts'),
    path('alerts/check/', views.CheckAlertsView.as_view(), name='check_alerts'),
    path('alerts/<uuid:alert_id>/resolve/', views.ResolveAlertView.as_view(), name='resolve_alert'),
    path('alerts/<uuid:alert_id>/resolve/form/', views.ResolveAlertFormView.as_view(), name='resolve_alert_form'),
    path('alerts/<uuid:alert_id>/dismiss/', views.DismissAlertView.as_view(), name='dismiss_alert'),

    # Reports
    path('reports/<uuid:student_id>/generate/', views.GenerateReportView.as_view(), name='generate_report'),
    path('reports/bulk-generate/', views.BulkGenerateReportsView.as_view(), name='bulk_generate_reports'),

    # Export
    path('export/csv/', views.ExportCSVView.as_view(), name='export_csv'),
]
```

---

## MODELS UPDATE

**File**: `apps/attendance/models.py` (rozszerzenie)

```python
from django.db import models
from django.conf import settings
import uuid


class AttendanceAlert(models.Model):
    """Model for low attendance alerts."""

    ALERT_TYPE_CHOICES = [
        ('LOW_ATTENDANCE', 'Niska frekwencja'),
        ('CONSECUTIVE_ABSENCE', 'Kolejne nieobecności'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Oczekujący'),
        ('RESOLVED', 'Rozwiązany'),
        ('DISMISSED', 'Odrzucony'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='attendance_alerts'
    )
    attendance_rate = models.DecimalField('Frekwencja', max_digits=5, decimal_places=2)
    threshold = models.IntegerField('Próg', default=80)
    alert_type = models.CharField('Typ alertu', max_length=30, choices=ALERT_TYPE_CHOICES)
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='PENDING')
    resolution = models.TextField('Rozwiązanie', blank=True)
    resolved_at = models.DateTimeField('Data rozwiązania', null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'attendance_alerts'
        verbose_name = 'Alert frekwencji'
        verbose_name_plural = 'Alerty frekwencji'
        ordering = ['-created_at']

    def __str__(self):
        return f"Alert: {self.student.get_full_name()} - {self.attendance_rate}%"


class AttendanceReport(models.Model):
    """Model for monthly attendance reports."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='attendance_reports'
    )
    month = models.DateField('Miesiąc')
    attendance_rate = models.DecimalField('Frekwencja', max_digits=5, decimal_places=2)
    total_lessons = models.IntegerField('Łączna liczba lekcji')
    present_count = models.IntegerField('Obecności')
    absent_count = models.IntegerField('Nieobecności')
    late_count = models.IntegerField('Spóźnienia')
    excused_count = models.IntegerField('Usprawiedliwienia')
    pdf_path = models.CharField('Ścieżka PDF', max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'attendance_reports'
        verbose_name = 'Raport frekwencji'
        verbose_name_plural = 'Raporty frekwencji'
        unique_together = ['student', 'month']
        ordering = ['-month']

    def __str__(self):
        return f"Raport: {self.student.get_full_name()} - {self.month.strftime('%B %Y')}"
```

---

## REQUIREMENTS

**File**: `requirements/base.txt` (rozszerzenie)

```txt
# ... existing requirements ...

# PDF generation
WeasyPrint>=60.0
```

---

## COMPLETION CHECKLIST

- [ ] Attendance statistics calculated correctly
- [ ] Weekly trend chart functional
- [ ] Subject breakdown working
- [ ] Low attendance alerts generated at <80%
- [ ] Admin notifications sent
- [ ] Parent notifications sent
- [ ] Alert resolution workflow functional
- [ ] Monthly PDF reports generated
- [ ] Reports sent via email
- [ ] CSV export with custom filters
- [ ] Excel-compatible encoding (BOM)
- [ ] Weekly summaries scheduled
- [ ] Absence alerts immediate
- [ ] Parent portal access grant working

---

**Next Phase**: Phase 6 - Cancellations & Makeup Lessons
