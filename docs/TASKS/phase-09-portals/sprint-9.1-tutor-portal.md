# Phase 9 - Sprint 9.1: Tutor Portal (Django)

## Tasks 108-112: Dedicated Tutor Dashboard & Management Tools

> **Duration**: Week 13 (Days 1-2)
> **Goal**: Complete tutor-facing portal with dashboard, lesson management, student tracking, and earnings
> **Dependencies**: Phase 1-8 completed

---

## SPRINT OVERVIEW

| Task ID | Description                               | Priority | Dependencies     |
| ------- | ----------------------------------------- | -------- | ---------------- |
| 108     | Tutor dashboard with widgets and overview | Critical | Phase 8 complete |
| 109     | My lessons view with quick actions        | Critical | Task 108         |
| 110     | My students list with progress tracking   | High     | Task 109         |
| 111     | Quick attendance management interface     | High     | Task 110         |
| 112     | Stats & earnings summary                  | High     | Task 111         |

---

## TUTOR DASHBOARD SERVICE

### Dashboard Data Service

**File**: `apps/tutors/services.py`

```python
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from apps.lessons.models import Lesson, LessonStudent
from apps.attendance.models import Attendance


class TutorDashboardService:
    """Serwis do obsługi dashboardu korepetytora."""

    @classmethod
    def get_dashboard_stats(cls, tutor):
        """Pobiera statystyki dla dashboardu."""

        today = timezone.now().date()
        month_start = today.replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        # Dzisiejsze zajęcia
        today_lessons = Lesson.objects.filter(
            tutor=tutor,
            start_time__date=today,
            status__in=['SCHEDULED', 'ONGOING', 'COMPLETED']
        )

        today_count = today_lessons.count()
        today_completed = today_lessons.filter(status='COMPLETED').count()

        # Uczniowie
        total_students = LessonStudent.objects.filter(
            lesson__tutor=tutor
        ).values('student').distinct().count()

        # Godziny w tym miesiącu
        monthly_lessons = Lesson.objects.filter(
            tutor=tutor,
            start_time__date__gte=month_start,
            start_time__date__lte=month_end,
            status='COMPLETED'
        )

        monthly_hours = sum(
            (l.end_time - l.start_time).total_seconds() / 3600
            for l in monthly_lessons
        )

        # Zarobki
        monthly_earnings = cls._calculate_monthly_earnings(tutor, month_start, month_end)
        previous_earnings = cls._calculate_monthly_earnings(
            tutor,
            (month_start - timedelta(days=1)).replace(day=1),
            month_start - timedelta(days=1)
        )

        earnings_growth = 0
        if previous_earnings > 0:
            earnings_growth = ((monthly_earnings - previous_earnings) / previous_earnings) * 100

        return {
            'today_lessons_count': today_count,
            'today_completed_count': today_completed,
            'total_students': total_students,
            'monthly_hours': round(monthly_hours, 1),
            'monthly_lessons_count': monthly_lessons.count(),
            'monthly_earnings': monthly_earnings,
            'earnings_growth': round(earnings_growth, 1),
        }

    @classmethod
    def _calculate_monthly_earnings(cls, tutor, start_date, end_date):
        """Oblicza zarobki za dany okres."""

        completed_lessons = Lesson.objects.filter(
            tutor=tutor,
            start_time__date__gte=start_date,
            start_time__date__lte=end_date,
            status='COMPLETED'
        )

        total = Decimal('0.00')
        hourly_rate = tutor.tutor_profile.hourly_rate if hasattr(tutor, 'tutor_profile') else Decimal('100.00')

        for lesson in completed_lessons:
            hours = (lesson.end_time - lesson.start_time).total_seconds() / 3600
            total += Decimal(str(hours)) * hourly_rate

        return float(total)

    @classmethod
    def get_today_lessons(cls, tutor):
        """Pobiera dzisiejsze zajęcia korepetytora."""

        today = timezone.now().date()

        return Lesson.objects.filter(
            tutor=tutor,
            start_time__date=today
        ).select_related(
            'subject', 'room'
        ).prefetch_related(
            'students__user'
        ).order_by('start_time')

    @classmethod
    def get_week_lessons(cls, tutor, start_date, end_date):
        """Pobiera zajęcia na dany tydzień."""

        return Lesson.objects.filter(
            tutor=tutor,
            start_time__date__gte=start_date,
            start_time__date__lte=end_date
        ).select_related(
            'subject', 'room'
        ).order_by('start_time')

    @classmethod
    def get_my_students(cls, tutor, limit=None):
        """Pobiera listę uczniów korepetytora."""

        from django.contrib.auth import get_user_model
        User = get_user_model()

        student_ids = LessonStudent.objects.filter(
            lesson__tutor=tutor
        ).values_list('student_id', flat=True).distinct()

        students = User.objects.filter(
            id__in=student_ids,
            is_active=True
        ).select_related('student_profile')

        # Dodaj statystyki
        student_data = []
        for student in students:
            attendance_stats = cls._get_student_attendance_stats(tutor, student)
            lesson_stats = cls._get_student_lesson_stats(tutor, student)

            student_data.append({
                'id': student.id,
                'name': student.first_name,
                'surname': student.last_name,
                'avatar': student.avatar.url if student.avatar else None,
                'class_name': student.student_profile.class_name if hasattr(student, 'student_profile') else None,
                'attendance_rate': attendance_stats['rate'],
                'total_lessons': lesson_stats['total'],
                'upcoming_lessons': lesson_stats['upcoming'],
                'last_lesson_date': lesson_stats['last_date'],
            })

        # Sortuj po nazwisku
        student_data.sort(key=lambda x: x['surname'])

        if limit:
            student_data = student_data[:limit]

        return student_data

    @classmethod
    def _get_student_attendance_stats(cls, tutor, student):
        """Oblicza statystyki obecności ucznia u korepetytora."""

        attendance = Attendance.objects.filter(
            lesson__tutor=tutor,
            student=student
        )

        total = attendance.count()
        present = attendance.filter(status__in=['PRESENT', 'LATE']).count()

        return {
            'rate': round((present / total) * 100, 1) if total > 0 else 0,
            'total': total,
            'present': present,
        }

    @classmethod
    def _get_student_lesson_stats(cls, tutor, student):
        """Oblicza statystyki zajęć ucznia u korepetytora."""

        now = timezone.now()

        lessons = Lesson.objects.filter(
            tutor=tutor,
            students__user=student
        )

        total = lessons.filter(status='COMPLETED').count()
        upcoming = lessons.filter(
            status='SCHEDULED',
            start_time__gt=now
        ).count()

        last_lesson = lessons.filter(
            status='COMPLETED'
        ).order_by('-start_time').first()

        return {
            'total': total,
            'upcoming': upcoming,
            'last_date': last_lesson.start_time.date() if last_lesson else None,
        }


class TutorEarningsService:
    """Serwis do obsługi zarobków korepetytora."""

    @classmethod
    def get_earnings_stats(cls, tutor, month_year: str):
        """Pobiera statystyki zarobków za miesiąc."""

        year, month = map(int, month_year.split('-'))
        month_start = timezone.datetime(year, month, 1).date()
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        # Poprzedni miesiąc
        prev_month_end = month_start - timedelta(days=1)
        prev_month_start = prev_month_end.replace(day=1)

        completed_lessons = Lesson.objects.filter(
            tutor=tutor,
            start_time__date__gte=month_start,
            start_time__date__lte=month_end,
            status='COMPLETED'
        )

        prev_lessons = Lesson.objects.filter(
            tutor=tutor,
            start_time__date__gte=prev_month_start,
            start_time__date__lte=prev_month_end,
            status='COMPLETED'
        )

        hourly_rate = tutor.tutor_profile.hourly_rate if hasattr(tutor, 'tutor_profile') else Decimal('100.00')

        # Oblicz godziny
        hours_this_month = sum(
            (l.end_time - l.start_time).total_seconds() / 3600
            for l in completed_lessons
        )

        # Oblicz zarobki
        current_month = float(Decimal(str(hours_this_month)) * hourly_rate)
        prev_hours = sum(
            (l.end_time - l.start_time).total_seconds() / 3600
            for l in prev_lessons
        )
        previous_month = float(Decimal(str(prev_hours)) * hourly_rate)

        # Zajęcia indywidualne vs grupowe
        individual = completed_lessons.filter(is_group=False).count()
        group = completed_lessons.filter(is_group=True).count()

        # Średnia tygodniowa
        weeks = 4
        avg_hours_per_week = hours_this_month / weeks if hours_this_month > 0 else 0

        return {
            'current_month': current_month,
            'previous_month': previous_month,
            'hours_this_month': round(hours_this_month, 1),
            'avg_hours_per_week': round(avg_hours_per_week, 1),
            'hourly_rate': float(hourly_rate),
            'effective_hourly_rate': current_month / hours_this_month if hours_this_month > 0 else 0,
            'lessons_completed': completed_lessons.count(),
            'lessons_individual': individual,
            'lessons_group': group,
        }

    @classmethod
    def get_earnings_breakdown(cls, tutor, start_date, end_date):
        """Pobiera podział zarobków wg przedmiotów."""

        completed_lessons = Lesson.objects.filter(
            tutor=tutor,
            start_time__date__gte=start_date,
            start_time__date__lte=end_date,
            status='COMPLETED'
        ).select_related('subject')

        hourly_rate = tutor.tutor_profile.hourly_rate if hasattr(tutor, 'tutor_profile') else Decimal('100.00')

        breakdown = {}
        for lesson in completed_lessons:
            subject_name = lesson.subject.name if lesson.subject else 'Inne'
            hours = (lesson.end_time - lesson.start_time).total_seconds() / 3600

            if subject_name not in breakdown:
                breakdown[subject_name] = {
                    'subject': subject_name,
                    'lessons': 0,
                    'hours': 0,
                    'amount': 0,
                    'hourly_rate': float(hourly_rate),
                }

            breakdown[subject_name]['lessons'] += 1
            breakdown[subject_name]['hours'] += hours
            breakdown[subject_name]['amount'] += float(Decimal(str(hours)) * hourly_rate)

        # Zaokrąglij wartości
        for key in breakdown:
            breakdown[key]['hours'] = round(breakdown[key]['hours'], 1)
            breakdown[key]['amount'] = round(breakdown[key]['amount'], 2)

        return list(breakdown.values())
```

---

## TUTOR VIEWS

### Dashboard Views

**File**: `apps/tutors/views.py`

```python
from django.views.generic import TemplateView, ListView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta

from apps.core.mixins import TutorRequiredMixin, HTMXMixin
from apps.lessons.models import Lesson
from apps.attendance.models import Attendance
from .services import TutorDashboardService, TutorEarningsService


class TutorDashboardView(LoginRequiredMixin, TutorRequiredMixin, TemplateView):
    """Dashboard korepetytora."""

    template_name = 'tutor_panel/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tutor = self.request.user

        today = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)

        context['stats'] = TutorDashboardService.get_dashboard_stats(tutor)
        context['today_lessons'] = TutorDashboardService.get_today_lessons(tutor)
        context['week_lessons'] = TutorDashboardService.get_week_lessons(
            tutor, week_start, week_end
        )
        context['recent_students'] = TutorDashboardService.get_my_students(tutor, limit=5)
        context['today'] = today
        context['week_start'] = week_start
        context['week_end'] = week_end

        return context


class TutorLessonsView(LoginRequiredMixin, TutorRequiredMixin, HTMXMixin, TemplateView):
    """Widok zajęć korepetytora."""

    template_name = 'tutor_panel/lessons/list.html'
    partial_template_name = 'tutor_panel/lessons/partials/_lesson_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tutor = self.request.user

        view_type = self.request.GET.get('view', 'calendar')
        context['view_type'] = view_type

        if view_type == 'list':
            context['lessons'] = Lesson.objects.filter(
                tutor=tutor
            ).select_related(
                'subject', 'room'
            ).prefetch_related(
                'students__user'
            ).order_by('-start_time')[:50]

        return context


class TutorCalendarEventsView(LoginRequiredMixin, TutorRequiredMixin, View):
    """API dla kalendarza korepetytora (FullCalendar)."""

    def get(self, request):
        import json
        from django.http import JsonResponse

        tutor = request.user
        start = request.GET.get('start')
        end = request.GET.get('end')

        lessons = Lesson.objects.filter(
            tutor=tutor,
            start_time__gte=start,
            end_time__lte=end
        ).select_related('subject', 'room')

        events = []
        for lesson in lessons:
            color = lesson.subject.color if lesson.subject and lesson.subject.color else '#3B82F6'
            if lesson.status == 'COMPLETED':
                color = '#22C55E'
            elif lesson.status == 'CANCELLED':
                color = '#EF4444'

            events.append({
                'id': str(lesson.id),
                'title': lesson.title,
                'start': lesson.start_time.isoformat(),
                'end': lesson.end_time.isoformat(),
                'backgroundColor': color,
                'borderColor': color,
                'extendedProps': {
                    'subject': lesson.subject.name if lesson.subject else '',
                    'room': lesson.room.name if lesson.room else 'Online',
                    'status': lesson.status,
                    'students_count': lesson.students.count(),
                }
            })

        return JsonResponse(events, safe=False)


class TutorLessonDetailView(LoginRequiredMixin, TutorRequiredMixin, View):
    """Szczegóły zajęć dla modala."""

    def get(self, request, lesson_id):
        lesson = get_object_or_404(
            Lesson.objects.select_related('subject', 'room').prefetch_related(
                'students__user',
                'attendance_records'
            ),
            id=lesson_id,
            tutor=request.user
        )

        html = render_to_string(
            'tutor_panel/lessons/partials/_lesson_detail_modal.html',
            {'lesson': lesson},
            request=request
        )

        return HttpResponse(html)


class TutorStudentsView(LoginRequiredMixin, TutorRequiredMixin, HTMXMixin, TemplateView):
    """Lista uczniów korepetytora."""

    template_name = 'tutor_panel/students/list.html'
    partial_template_name = 'tutor_panel/students/partials/_student_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tutor = self.request.user

        search = self.request.GET.get('search', '')
        sort_by = self.request.GET.get('sort', 'name')
        class_filter = self.request.GET.get('class', '')

        students = TutorDashboardService.get_my_students(tutor)

        # Filtrowanie
        if search:
            search_lower = search.lower()
            students = [
                s for s in students
                if search_lower in s['name'].lower() or search_lower in s['surname'].lower()
            ]

        if class_filter:
            students = [s for s in students if s['class_name'] == class_filter]

        # Sortowanie
        if sort_by == 'attendance':
            students.sort(key=lambda x: x['attendance_rate'], reverse=True)
        elif sort_by == 'recent':
            students.sort(
                key=lambda x: x['last_lesson_date'] or timezone.datetime.min.date(),
                reverse=True
            )

        context['students'] = students

        # Unikalne klasy dla filtra
        all_students = TutorDashboardService.get_my_students(tutor)
        context['classes'] = sorted(set(
            s['class_name'] for s in all_students if s['class_name']
        ))

        return context


class TutorStudentDetailView(LoginRequiredMixin, TutorRequiredMixin, TemplateView):
    """Szczegóły ucznia."""

    template_name = 'tutor_panel/students/detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from django.contrib.auth import get_user_model
        User = get_user_model()

        student_id = kwargs.get('student_id')
        student = get_object_or_404(User, id=student_id)

        tutor = self.request.user

        # Sprawdź czy uczeń jest przypisany do tego korepetytora
        is_my_student = Lesson.objects.filter(
            tutor=tutor,
            students__user=student
        ).exists()

        if not is_my_student:
            from django.http import Http404
            raise Http404("Uczeń nie jest Twoim podopiecznym")

        # Statystyki
        context['student'] = student
        context['attendance_stats'] = TutorDashboardService._get_student_attendance_stats(tutor, student)
        context['lesson_stats'] = TutorDashboardService._get_student_lesson_stats(tutor, student)

        # Historia zajęć
        context['lessons'] = Lesson.objects.filter(
            tutor=tutor,
            students__user=student
        ).select_related('subject').order_by('-start_time')[:20]

        # Historia obecności
        context['attendance_history'] = Attendance.objects.filter(
            lesson__tutor=tutor,
            student=student
        ).select_related('lesson').order_by('-lesson__start_time')[:20]

        return context


class TutorQuickAttendanceView(LoginRequiredMixin, TutorRequiredMixin, View):
    """Szybkie oznaczanie obecności."""

    def get(self, request, lesson_id):
        """Wyświetla formularz obecności."""

        lesson = get_object_or_404(
            Lesson.objects.prefetch_related('students__user'),
            id=lesson_id,
            tutor=request.user
        )

        # Pobierz istniejące rekordy obecności
        existing_attendance = {
            a.student_id: a.status
            for a in Attendance.objects.filter(lesson=lesson)
        }

        students_data = []
        for ls in lesson.students.all():
            students_data.append({
                'id': ls.user.id,
                'name': ls.user.first_name,
                'surname': ls.user.last_name,
                'current_status': existing_attendance.get(ls.user.id, 'PRESENT'),
            })

        html = render_to_string(
            'tutor_panel/attendance/partials/_quick_attendance_form.html',
            {
                'lesson': lesson,
                'students': students_data,
            },
            request=request
        )

        return HttpResponse(html)

    def post(self, request, lesson_id):
        """Zapisuje obecność."""

        lesson = get_object_or_404(Lesson, id=lesson_id, tutor=request.user)

        for key, value in request.POST.items():
            if key.startswith('attendance_'):
                student_id = key.replace('attendance_', '')
                status = value

                Attendance.objects.update_or_create(
                    lesson=lesson,
                    student_id=student_id,
                    defaults={
                        'status': status,
                        'marked_by': request.user,
                        'marked_at': timezone.now(),
                    }
                )

        return HttpResponse(
            status=204,
            headers={'HX-Trigger': 'attendanceSaved'}
        )


class TutorEarningsView(LoginRequiredMixin, TutorRequiredMixin, TemplateView):
    """Widok zarobków korepetytora."""

    template_name = 'tutor_panel/earnings/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tutor = self.request.user

        today = timezone.now().date()
        selected_month = self.request.GET.get('month', today.strftime('%Y-%m'))

        context['selected_month'] = selected_month
        context['stats'] = TutorEarningsService.get_earnings_stats(tutor, selected_month)

        # Podział zarobków
        year, month = map(int, selected_month.split('-'))
        month_start = timezone.datetime(year, month, 1).date()
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        context['breakdown'] = TutorEarningsService.get_earnings_breakdown(
            tutor, month_start, month_end
        )

        # Ostatnie 12 miesięcy dla selektora
        from dateutil.relativedelta import relativedelta
        context['month_options'] = [
            {
                'value': (today - relativedelta(months=i)).strftime('%Y-%m'),
                'label': (today - relativedelta(months=i)).strftime('%B %Y'),
            }
            for i in range(12)
        ]

        return context
```

---

## TUTOR TEMPLATES

### Dashboard Template

**File**: `templates/tutor_panel/dashboard.html`

```html
{% extends "tutor_panel/base.html" %}

{% block content %}
<div class="space-y-6">
    <!-- Header -->
    <div>
        <h1 class="text-3xl font-bold">Witaj, {{ request.user.first_name }}!</h1>
        <p class="text-gray-600 mt-1">Twój panel korepetytora - wszystko w jednym miejscu</p>
    </div>

    <!-- Stats Cards -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div class="card bg-base-100 shadow">
            <div class="card-body">
                <div class="flex items-center justify-between">
                    <h2 class="card-title text-sm font-medium">Dzisiejsze zajęcia</h2>
                    <svg class="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                    </svg>
                </div>
                <div class="text-2xl font-bold">{{ stats.today_lessons_count }}</div>
                <p class="text-xs text-gray-600">{{ stats.today_completed_count }} zakończone</p>
            </div>
        </div>

        <div class="card bg-base-100 shadow">
            <div class="card-body">
                <div class="flex items-center justify-between">
                    <h2 class="card-title text-sm font-medium">Moi uczniowie</h2>
                    <svg class="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z"></path>
                    </svg>
                </div>
                <div class="text-2xl font-bold">{{ stats.total_students }}</div>
                <p class="text-xs text-gray-600">aktywnych uczniów</p>
            </div>
        </div>

        <div class="card bg-base-100 shadow">
            <div class="card-body">
                <div class="flex items-center justify-between">
                    <h2 class="card-title text-sm font-medium">Godziny w tym miesiącu</h2>
                    <svg class="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                </div>
                <div class="text-2xl font-bold">{{ stats.monthly_hours }}h</div>
                <p class="text-xs text-gray-600">{{ stats.monthly_lessons_count }} zajęć</p>
            </div>
        </div>

        <div class="card bg-base-100 shadow">
            <div class="card-body">
                <div class="flex items-center justify-between">
                    <h2 class="card-title text-sm font-medium">Zarobki w tym miesiącu</h2>
                    <svg class="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path>
                    </svg>
                </div>
                <div class="text-2xl font-bold">{{ stats.monthly_earnings|floatformat:0 }} zł</div>
                <p class="text-xs {% if stats.earnings_growth >= 0 %}text-success{% else %}text-error{% endif %}">
                    {% if stats.earnings_growth >= 0 %}+{% endif %}{{ stats.earnings_growth }}% vs poprzedni miesiąc
                </p>
            </div>
        </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Today's Lessons -->
        <div class="lg:col-span-2">
            <div class="card bg-base-100 shadow">
                <div class="card-body">
                    <h2 class="card-title">Dzisiejsze zajęcia</h2>
                    <p class="text-sm text-gray-600">{{ today|date:"l, j F Y" }}</p>

                    {% if today_lessons %}
                    <div class="space-y-3 mt-4">
                        {% for lesson in today_lessons %}
                        <div class="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 transition-colors">
                            <div class="flex-1">
                                <div class="flex items-center space-x-2">
                                    <h4 class="font-medium">{{ lesson.title }}</h4>
                                    <span class="badge {% if lesson.status == 'COMPLETED' %}badge-success{% elif lesson.status == 'ONGOING' %}badge-primary{% else %}badge-ghost{% endif %}">
                                        {% if lesson.status == 'COMPLETED' %}Zakończone{% elif lesson.status == 'ONGOING' %}W trakcie{% else %}Zaplanowane{% endif %}
                                    </span>
                                </div>
                                <div class="flex items-center space-x-4 mt-2 text-sm text-gray-600">
                                    <span>{{ lesson.start_time|time:"H:i" }} - {{ lesson.end_time|time:"H:i" }}</span>
                                    <span>{{ lesson.room.name|default:"Online" }}</span>
                                    <span>{{ lesson.students.count }} uczniów</span>
                                </div>
                            </div>

                            {% if lesson.status == 'SCHEDULED' %}
                            <button class="btn btn-sm btn-primary"
                                    hx-get="{% url 'tutor:quick_attendance' lesson.id %}"
                                    hx-target="#modal-content"
                                    onclick="document.getElementById('modal').showModal()">
                                Obecność
                            </button>
                            {% endif %}
                        </div>
                        {% endfor %}
                    </div>
                    {% else %}
                    <div class="text-center py-8 text-gray-500">
                        <svg class="mx-auto h-12 w-12 mb-2 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                        </svg>
                        <p>Brak zajęć na dzisiaj</p>
                        <p class="text-sm mt-1">Ciesz się wolnym dniem!</p>
                    </div>
                    {% endif %}
                </div>
            </div>
        </div>

        <!-- Recent Students -->
        <div>
            <div class="card bg-base-100 shadow">
                <div class="card-body">
                    <h2 class="card-title">Moi uczniowie</h2>
                    <p class="text-sm text-gray-600">Ostatnio aktywni</p>

                    {% if recent_students %}
                    <div class="space-y-3 mt-4">
                        {% for student in recent_students %}
                        <a href="{% url 'tutor:student_detail' student.id %}"
                           class="flex items-center space-x-3 p-3 border rounded-lg hover:bg-gray-50 transition-colors">
                            <div class="avatar placeholder">
                                <div class="bg-primary text-primary-content rounded-full w-10">
                                    <span class="text-sm">{{ student.name.0 }}{{ student.surname.0 }}</span>
                                </div>
                            </div>
                            <div class="flex-1 min-w-0">
                                <div class="font-medium truncate">{{ student.name }} {{ student.surname }}</div>
                                {% if student.class_name %}
                                <div class="text-sm text-gray-600">Klasa {{ student.class_name }}</div>
                                {% endif %}
                            </div>
                            <div class="text-right">
                                <div class="text-sm font-medium">{{ student.attendance_rate }}%</div>
                                <div class="text-xs text-gray-500">obecność</div>
                            </div>
                        </a>
                        {% endfor %}

                        <a href="{% url 'tutor:students' %}" class="btn btn-outline btn-sm w-full">
                            Zobacz wszystkich uczniów
                        </a>
                    </div>
                    {% else %}
                    <div class="text-center py-8 text-gray-500">
                        <p class="text-sm">Brak przypisanych uczniów</p>
                    </div>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>

    <!-- Quick Actions -->
    <div class="card bg-base-100 shadow">
        <div class="card-body">
            <h2 class="card-title">Szybkie akcje</h2>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4">
                <a href="{% url 'tutor:lessons' %}" class="btn btn-outline h-auto flex-col py-4">
                    <svg class="w-6 h-6 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                    </svg>
                    Moje zajęcia
                </a>

                <a href="{% url 'tutor:students' %}" class="btn btn-outline h-auto flex-col py-4">
                    <svg class="w-6 h-6 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z"></path>
                    </svg>
                    Uczniowie
                </a>

                <a href="{% url 'tutor:attendance' %}" class="btn btn-outline h-auto flex-col py-4">
                    <svg class="w-6 h-6 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                    Obecność
                </a>

                <a href="{% url 'tutor:earnings' %}" class="btn btn-outline h-auto flex-col py-4">
                    <svg class="w-6 h-6 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path>
                    </svg>
                    Zarobki
                </a>
            </div>
        </div>
    </div>
</div>

<!-- Modal -->
<dialog id="modal" class="modal">
    <div class="modal-box max-w-2xl">
        <div id="modal-content"></div>
    </div>
    <form method="dialog" class="modal-backdrop">
        <button>close</button>
    </form>
</dialog>
{% endblock %}
```

### Quick Attendance Form Partial

**File**: `templates/tutor_panel/attendance/partials/_quick_attendance_form.html`

```html
<form hx-post="{% url 'tutor:quick_attendance' lesson.id %}"
      hx-swap="none"
      hx-on::after-request="document.getElementById('modal').close()">
    {% csrf_token %}

    <h3 class="font-bold text-lg mb-4">Obecność - {{ lesson.title }}</h3>
    <p class="text-sm text-gray-600 mb-4">
        {{ lesson.start_time|date:"d.m.Y H:i" }} - {{ lesson.end_time|time:"H:i" }}
    </p>

    <!-- Quick Actions -->
    <div class="flex items-center space-x-2 mb-4">
        <span class="text-sm font-medium">Oznacz wszystkich:</span>
        <button type="button"
                class="btn btn-xs btn-success"
                onclick="setAllAttendance('PRESENT')">
            Obecni
        </button>
        <button type="button"
                class="btn btn-xs btn-error"
                onclick="setAllAttendance('ABSENT')">
            Nieobecni
        </button>
    </div>

    <!-- Students List -->
    <div class="space-y-3 max-h-96 overflow-y-auto">
        {% for student in students %}
        <div class="flex items-center justify-between p-3 border rounded-lg">
            <div class="flex items-center space-x-3">
                <div class="avatar placeholder">
                    <div class="bg-gray-200 text-gray-600 rounded-full w-10">
                        <span class="text-sm">{{ student.name.0 }}{{ student.surname.0 }}</span>
                    </div>
                </div>
                <div class="font-medium">{{ student.name }} {{ student.surname }}</div>
            </div>

            <div class="flex items-center space-x-1" data-student-id="{{ student.id }}">
                <input type="hidden"
                       name="attendance_{{ student.id }}"
                       value="{{ student.current_status }}"
                       class="attendance-input">

                <button type="button"
                        class="btn btn-sm {% if student.current_status == 'PRESENT' %}btn-success{% else %}btn-outline{% endif %}"
                        onclick="setAttendance('{{ student.id }}', 'PRESENT', this)"
                        title="Obecny">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                    </svg>
                </button>

                <button type="button"
                        class="btn btn-sm {% if student.current_status == 'LATE' %}btn-warning{% else %}btn-outline{% endif %}"
                        onclick="setAttendance('{{ student.id }}', 'LATE', this)"
                        title="Spóźniony">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                </button>

                <button type="button"
                        class="btn btn-sm {% if student.current_status == 'ABSENT' %}btn-error{% else %}btn-outline{% endif %}"
                        onclick="setAttendance('{{ student.id }}', 'ABSENT', this)"
                        title="Nieobecny">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                </button>

                <button type="button"
                        class="btn btn-sm {% if student.current_status == 'EXCUSED' %}btn-info{% else %}btn-outline{% endif %}"
                        onclick="setAttendance('{{ student.id }}', 'EXCUSED', this)"
                        title="Usprawiedliwiony">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                    </svg>
                </button>
            </div>
        </div>
        {% endfor %}
    </div>

    <div class="modal-action">
        <button type="button" class="btn btn-ghost" onclick="document.getElementById('modal').close()">
            Anuluj
        </button>
        <button type="submit" class="btn btn-primary">
            Zapisz obecność
        </button>
    </div>
</form>

<script>
function setAttendance(studentId, status, btn) {
    const container = btn.closest('[data-student-id]');
    const input = container.querySelector('.attendance-input');
    input.value = status;

    // Update button styles
    container.querySelectorAll('button').forEach(b => {
        b.classList.remove('btn-success', 'btn-warning', 'btn-error', 'btn-info');
        b.classList.add('btn-outline');
    });

    btn.classList.remove('btn-outline');
    if (status === 'PRESENT') btn.classList.add('btn-success');
    else if (status === 'LATE') btn.classList.add('btn-warning');
    else if (status === 'ABSENT') btn.classList.add('btn-error');
    else if (status === 'EXCUSED') btn.classList.add('btn-info');
}

function setAllAttendance(status) {
    document.querySelectorAll('[data-student-id]').forEach(container => {
        const input = container.querySelector('.attendance-input');
        input.value = status;

        container.querySelectorAll('button').forEach(b => {
            b.classList.remove('btn-success', 'btn-warning', 'btn-error', 'btn-info');
            b.classList.add('btn-outline');
        });

        const selector = status === 'PRESENT' ? '[title="Obecny"]' :
                        status === 'LATE' ? '[title="Spóźniony"]' :
                        status === 'ABSENT' ? '[title="Nieobecny"]' : '[title="Usprawiedliwiony"]';

        const btn = container.querySelector(selector);
        btn.classList.remove('btn-outline');
        if (status === 'PRESENT') btn.classList.add('btn-success');
        else if (status === 'LATE') btn.classList.add('btn-warning');
        else if (status === 'ABSENT') btn.classList.add('btn-error');
        else if (status === 'EXCUSED') btn.classList.add('btn-info');
    });
}
</script>
```

---

## URL CONFIGURATION

**File**: `apps/tutors/urls.py`

```python
from django.urls import path
from . import views

app_name = 'tutor'

urlpatterns = [
    path('', views.TutorDashboardView.as_view(), name='dashboard'),
    path('lessons/', views.TutorLessonsView.as_view(), name='lessons'),
    path('lessons/events/', views.TutorCalendarEventsView.as_view(), name='calendar_events'),
    path('lessons/<uuid:lesson_id>/', views.TutorLessonDetailView.as_view(), name='lesson_detail'),
    path('lessons/<uuid:lesson_id>/attendance/', views.TutorQuickAttendanceView.as_view(), name='quick_attendance'),
    path('students/', views.TutorStudentsView.as_view(), name='students'),
    path('students/<uuid:student_id>/', views.TutorStudentDetailView.as_view(), name='student_detail'),
    path('earnings/', views.TutorEarningsView.as_view(), name='earnings'),
]
```

---

## COMPLETION CHECKLIST

- [ ] Tutor dashboard operational
- [ ] All widgets displaying correctly
- [ ] Lessons calendar with FullCalendar working
- [ ] Student list with filtering and sorting
- [ ] Quick attendance marking functional
- [ ] Earnings statistics accurate
- [ ] All navigation working
- [ ] Mobile responsive design
- [ ] HTMX interactions smooth

---

**Next Sprint**: 9.2 - Student Portal
