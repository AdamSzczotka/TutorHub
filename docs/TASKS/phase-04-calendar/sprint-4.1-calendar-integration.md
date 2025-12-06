# Phase 4 - Sprint 4.1: Calendar Integration (Django)

## Tasks 054-059: FullCalendar Implementation & Event Management

> **Duration**: Week 7 (First half of Phase 4)
> **Goal**: Complete calendar system with drag & drop, event creation, and resource views
> **Dependencies**: Phase 1-3 completed (Database, Auth, Admin Panel)

---

## SPRINT OVERVIEW

| Task ID | Description                                | Priority | Dependencies     |
| ------- | ------------------------------------------ | -------- | ---------------- |
| 054     | FullCalendar setup with Django integration | Critical | Phase 3 complete |
| 055     | Calendar view with view switcher           | Critical | Task 054         |
| 056     | Drag & drop events functionality           | Critical | Task 055         |
| 057     | Event creation modal with HTMX             | Critical | Task 056         |
| 058     | Event colors system by subject/status      | High     | Task 057         |
| 059     | Resources view (room/tutor based)          | High     | Task 058         |

---

## FULLCALENDAR SETUP

### Static Files Configuration

**File**: `static/js/calendar/calendar-config.js`

```javascript
// static/js/calendar/calendar-config.js

// Polish localization
const polishLocale = {
    code: 'pl',
    week: {
        dow: 1, // Monday
        doy: 4,
    },
    buttonText: {
        prev: 'Poprzedni',
        next: 'Następny',
        today: 'Dziś',
        month: 'Miesiąc',
        week: 'Tydzień',
        day: 'Dzień',
        list: 'Lista',
    },
    weekText: 'Tyg',
    allDayText: 'Cały dzień',
    moreLinkText: 'więcej',
    noEventsText: 'Brak zajęć do wyświetlenia',
};

// Subject colors
const SUBJECT_COLORS = {
    'Matematyka': '#EF4444',
    'Język Polski': '#3B82F6',
    'Język Angielski': '#10B981',
    'Fizyka': '#8B5CF6',
    'Chemia': '#F59E0B',
    'Biologia': '#06B6D4',
    'Historia': '#84CC16',
    'Geografia': '#F97316',
};

// Status colors
const STATUS_COLORS = {
    'SCHEDULED': '#3B82F6',
    'ONGOING': '#10B981',
    'COMPLETED': '#6B7280',
    'CANCELLED': '#EF4444',
};

function getEventColor(subject, status, customColor) {
    if (customColor) return customColor;
    if (status === 'CANCELLED') return STATUS_COLORS.CANCELLED;
    if (status === 'COMPLETED') return STATUS_COLORS.COMPLETED;
    if (status === 'ONGOING') return STATUS_COLORS.ONGOING;
    return SUBJECT_COLORS[subject] || STATUS_COLORS.SCHEDULED;
}
```

### Calendar Alpine.js Component

**File**: `static/js/calendar/calendar-component.js`

```javascript
// static/js/calendar/calendar-component.js

function calendarApp() {
    return {
        calendar: null,
        currentView: 'timeGridWeek',
        isLoading: false,
        selectedEvent: null,

        init() {
            this.initCalendar();
            this.setupHTMXListeners();
        },

        initCalendar() {
            const calendarEl = document.getElementById('calendar');

            this.calendar = new FullCalendar.Calendar(calendarEl, {
                plugins: ['dayGrid', 'timeGrid', 'interaction', 'list'],
                initialView: this.currentView,
                locale: 'pl',
                timeZone: 'Europe/Warsaw',
                firstDay: 1,
                slotMinTime: '08:00:00',
                slotMaxTime: '20:00:00',
                height: 'auto',

                headerToolbar: {
                    left: 'prev,next today',
                    center: 'title',
                    right: 'dayGridMonth,timeGridWeek,timeGridDay,listWeek'
                },

                businessHours: {
                    daysOfWeek: [1, 2, 3, 4, 5, 6],
                    startTime: '08:00',
                    endTime: '18:00',
                },

                // Event source - fetch from Django
                events: {
                    url: '/api/calendar/events/',
                    method: 'GET',
                    extraParams: () => {
                        return {
                            view: this.currentView,
                        };
                    },
                    failure: () => {
                        this.showError('Błąd ładowania wydarzeń');
                    },
                },

                // Enable drag & drop
                editable: true,
                selectable: true,
                selectMirror: true,
                dayMaxEvents: true,

                // Event handlers
                eventClick: (info) => this.handleEventClick(info),
                select: (info) => this.handleDateSelect(info),
                eventDrop: (info) => this.handleEventDrop(info),
                eventResize: (info) => this.handleEventResize(info),

                // Custom event rendering
                eventDidMount: (info) => this.renderEventTooltip(info),

                // View change
                viewDidMount: (info) => {
                    this.currentView = info.view.type;
                },
            });

            this.calendar.render();
        },

        setupHTMXListeners() {
            // Refresh calendar after HTMX operations
            document.body.addEventListener('eventCreated', () => {
                this.calendar.refetchEvents();
                this.closeModal();
            });

            document.body.addEventListener('eventUpdated', () => {
                this.calendar.refetchEvents();
                this.closeModal();
            });

            document.body.addEventListener('eventDeleted', () => {
                this.calendar.refetchEvents();
                this.closeModal();
            });
        },

        handleEventClick(info) {
            this.selectedEvent = info.event;

            // Load event details via HTMX
            htmx.ajax('GET', `/admin/lessons/${info.event.id}/`, {
                target: '#modal-content',
                swap: 'innerHTML'
            });

            document.getElementById('event-modal').showModal();
        },

        handleDateSelect(info) {
            // Open create form with pre-filled dates
            const startTime = info.startStr;
            const endTime = info.endStr;

            htmx.ajax('GET', `/admin/lessons/create/?start=${startTime}&end=${endTime}`, {
                target: '#modal-content',
                swap: 'innerHTML'
            });

            document.getElementById('event-modal').showModal();
        },

        async handleEventDrop(info) {
            const { event, revert } = info;

            // Show loading state
            event.setProp('backgroundColor', '#94A3B8');

            try {
                const response = await fetch(`/api/calendar/events/${event.id}/move/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCSRFToken(),
                    },
                    body: JSON.stringify({
                        start_time: event.start.toISOString(),
                        end_time: event.end.toISOString(),
                    }),
                });

                const data = await response.json();

                if (!response.ok) {
                    revert();
                    this.showError(data.error || 'Nie udało się przesunąć zajęć');
                    return;
                }

                // Restore color and show success
                this.calendar.refetchEvents();
                this.showSuccess('Zajęcia zostały przesunięte');

            } catch (error) {
                revert();
                this.showError('Błąd połączenia z serwerem');
            }
        },

        async handleEventResize(info) {
            const { event, revert } = info;

            try {
                const response = await fetch(`/api/calendar/events/${event.id}/resize/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCSRFToken(),
                    },
                    body: JSON.stringify({
                        end_time: event.end.toISOString(),
                    }),
                });

                if (!response.ok) {
                    revert();
                    const data = await response.json();
                    this.showError(data.error || 'Nie udało się zmienić czasu trwania');
                    return;
                }

                this.showSuccess('Czas trwania został zmieniony');

            } catch (error) {
                revert();
                this.showError('Błąd połączenia z serwerem');
            }
        },

        renderEventTooltip(info) {
            const props = info.event.extendedProps;

            tippy(info.el, {
                content: `
                    <div class="p-2 text-sm">
                        <div class="font-semibold">${info.event.title}</div>
                        <div>Przedmiot: ${props.subject || 'N/A'}</div>
                        <div>Korepetytor: ${props.tutor || 'N/A'}</div>
                        <div>Sala: ${props.room || 'Online'}</div>
                        <div>Uczniów: ${props.student_count || 0}</div>
                    </div>
                `,
                allowHTML: true,
                theme: 'light-border',
            });
        },

        changeView(view) {
            this.currentView = view;
            this.calendar.changeView(view);
        },

        goToToday() {
            this.calendar.today();
        },

        closeModal() {
            document.getElementById('event-modal').close();
            this.selectedEvent = null;
        },

        getCSRFToken() {
            return document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
                   document.cookie.match(/csrftoken=([^;]+)/)?.[1];
        },

        showSuccess(message) {
            // Use toast notification
            const toast = document.createElement('div');
            toast.className = 'toast toast-end';
            toast.innerHTML = `<div class="alert alert-success"><span>${message}</span></div>`;
            document.body.appendChild(toast);
            setTimeout(() => toast.remove(), 3000);
        },

        showError(message) {
            const toast = document.createElement('div');
            toast.className = 'toast toast-end';
            toast.innerHTML = `<div class="alert alert-error"><span>${message}</span></div>`;
            document.body.appendChild(toast);
            setTimeout(() => toast.remove(), 5000);
        },
    };
}
```

---

## DJANGO VIEWS

### Calendar API Views

**File**: `apps/lessons/api_views.py`

```python
from django.http import JsonResponse
from django.views import View
from django.views.decorators.http import require_http_methods
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.utils import timezone
from datetime import datetime, timedelta
import json

from apps.core.mixins import AdminRequiredMixin
from .models import Lesson, LessonStudent
from .services import CalendarService


class CalendarEventsAPIView(LoginRequiredMixin, View):
    """API endpoint for FullCalendar events."""

    def get(self, request):
        start = request.GET.get('start')
        end = request.GET.get('end')
        tutor_id = request.GET.get('tutor_id')
        room_id = request.GET.get('room_id')

        filters = {
            'deleted_at__isnull': True,
        }

        if start:
            filters['start_time__gte'] = datetime.fromisoformat(start.replace('Z', '+00:00'))
        if end:
            filters['end_time__lte'] = datetime.fromisoformat(end.replace('Z', '+00:00'))
        if tutor_id:
            filters['tutor_id'] = tutor_id
        if room_id:
            filters['room_id'] = room_id

        # Filter based on user role
        user = request.user
        if user.role == 'TUTOR':
            filters['tutor_id'] = user.id
        elif user.role == 'STUDENT':
            lessons = Lesson.objects.filter(
                lesson_students__student_id=user.id,
                **filters
            )
        else:
            lessons = Lesson.objects.filter(**filters)

        if user.role != 'STUDENT':
            lessons = Lesson.objects.filter(**filters)

        lessons = lessons.select_related(
            'subject', 'level', 'tutor', 'room'
        ).prefetch_related('lesson_students__student')

        events = []
        for lesson in lessons:
            events.append({
                'id': str(lesson.id),
                'title': lesson.title,
                'start': lesson.start_time.isoformat(),
                'end': lesson.end_time.isoformat(),
                'backgroundColor': self._get_color(lesson),
                'borderColor': self._get_color(lesson),
                'extendedProps': {
                    'subject': lesson.subject.name if lesson.subject else None,
                    'level': lesson.level.name if lesson.level else None,
                    'tutor': f"{lesson.tutor.first_name} {lesson.tutor.last_name}" if lesson.tutor else None,
                    'room': lesson.room.name if lesson.room else None,
                    'status': lesson.status,
                    'is_group_lesson': lesson.is_group_lesson,
                    'max_participants': lesson.max_participants,
                    'student_count': lesson.lesson_students.count(),
                },
            })

        return JsonResponse(events, safe=False)

    def _get_color(self, lesson):
        status_colors = {
            'SCHEDULED': '#3B82F6',
            'ONGOING': '#10B981',
            'COMPLETED': '#6B7280',
            'CANCELLED': '#EF4444',
        }

        subject_colors = {
            'Matematyka': '#EF4444',
            'Język Polski': '#3B82F6',
            'Język Angielski': '#10B981',
            'Fizyka': '#8B5CF6',
            'Chemia': '#F59E0B',
        }

        if lesson.color:
            return lesson.color
        if lesson.status in ['CANCELLED', 'COMPLETED']:
            return status_colors.get(lesson.status, '#3B82F6')
        if lesson.subject:
            return subject_colors.get(lesson.subject.name, '#3B82F6')
        return '#3B82F6'


@method_decorator(csrf_protect, name='dispatch')
class EventMoveAPIView(LoginRequiredMixin, AdminRequiredMixin, View):
    """API endpoint for moving events (drag & drop)."""

    def post(self, request, pk):
        try:
            data = json.loads(request.body)
            start_time = datetime.fromisoformat(data['start_time'].replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(data['end_time'].replace('Z', '+00:00'))

            lesson = Lesson.objects.get(pk=pk)

            # Check for conflicts
            calendar_service = CalendarService()
            conflicts = calendar_service.check_conflicts(
                tutor_id=lesson.tutor_id,
                room_id=lesson.room_id,
                start_time=start_time,
                end_time=end_time,
                exclude_lesson_id=lesson.id
            )

            if conflicts:
                conflict_titles = [c.title for c in conflicts]
                return JsonResponse({
                    'error': f'Konflikt z zajęciami: {", ".join(conflict_titles)}'
                }, status=400)

            lesson.start_time = start_time
            lesson.end_time = end_time
            lesson.save()

            return JsonResponse({'success': True})

        except Lesson.DoesNotExist:
            return JsonResponse({'error': 'Zajęcia nie istnieją'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


@method_decorator(csrf_protect, name='dispatch')
class EventResizeAPIView(LoginRequiredMixin, AdminRequiredMixin, View):
    """API endpoint for resizing events."""

    def post(self, request, pk):
        try:
            data = json.loads(request.body)
            end_time = datetime.fromisoformat(data['end_time'].replace('Z', '+00:00'))

            lesson = Lesson.objects.get(pk=pk)

            # Check for conflicts
            calendar_service = CalendarService()
            conflicts = calendar_service.check_conflicts(
                tutor_id=lesson.tutor_id,
                room_id=lesson.room_id,
                start_time=lesson.start_time,
                end_time=end_time,
                exclude_lesson_id=lesson.id
            )

            if conflicts:
                return JsonResponse({
                    'error': 'Konflikt z innymi zajęciami'
                }, status=400)

            lesson.end_time = end_time
            lesson.save()

            return JsonResponse({'success': True})

        except Lesson.DoesNotExist:
            return JsonResponse({'error': 'Zajęcia nie istnieją'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
```

### Calendar Service

**File**: `apps/lessons/services.py`

```python
from django.db.models import Q
from datetime import datetime, timedelta
from typing import List, Optional
from .models import Lesson


class CalendarService:
    """Service for calendar operations and conflict detection."""

    def check_conflicts(
        self,
        tutor_id: str,
        start_time: datetime,
        end_time: datetime,
        room_id: Optional[str] = None,
        exclude_lesson_id: Optional[str] = None
    ) -> List[Lesson]:
        """Check for scheduling conflicts."""

        base_query = Lesson.objects.filter(
            deleted_at__isnull=True,
            status__in=['SCHEDULED', 'ONGOING']
        )

        if exclude_lesson_id:
            base_query = base_query.exclude(pk=exclude_lesson_id)

        # Build resource conflict query
        resource_query = Q(tutor_id=tutor_id)
        if room_id:
            resource_query |= Q(room_id=room_id)

        # Time overlap conditions
        time_overlap = (
            Q(start_time__lt=end_time, end_time__gt=start_time)
        )

        conflicts = base_query.filter(resource_query & time_overlap).select_related(
            'subject', 'tutor', 'room'
        )

        return list(conflicts)

    def check_tutor_availability(
        self,
        tutor_id: str,
        start_time: datetime,
        end_time: datetime,
        exclude_lesson_id: Optional[str] = None
    ) -> bool:
        """Check if tutor is available."""
        conflicts = self.check_conflicts(
            tutor_id=tutor_id,
            start_time=start_time,
            end_time=end_time,
            exclude_lesson_id=exclude_lesson_id
        )
        return len(conflicts) == 0

    def check_room_availability(
        self,
        room_id: str,
        start_time: datetime,
        end_time: datetime,
        exclude_lesson_id: Optional[str] = None
    ) -> bool:
        """Check if room is available."""
        conflicts = Lesson.objects.filter(
            room_id=room_id,
            deleted_at__isnull=True,
            status__in=['SCHEDULED', 'ONGOING'],
            start_time__lt=end_time,
            end_time__gt=start_time
        )

        if exclude_lesson_id:
            conflicts = conflicts.exclude(pk=exclude_lesson_id)

        return not conflicts.exists()

    def check_student_availability(
        self,
        student_id: str,
        start_time: datetime,
        end_time: datetime,
        exclude_lesson_id: Optional[str] = None
    ) -> bool:
        """Check if student is available."""
        conflicts = Lesson.objects.filter(
            lesson_students__student_id=student_id,
            deleted_at__isnull=True,
            status__in=['SCHEDULED', 'ONGOING'],
            start_time__lt=end_time,
            end_time__gt=start_time
        )

        if exclude_lesson_id:
            conflicts = conflicts.exclude(pk=exclude_lesson_id)

        return not conflicts.exists()

    def find_available_slots(
        self,
        tutor_id: str,
        date: datetime,
        duration_minutes: int = 60
    ) -> List[dict]:
        """Find available time slots for a tutor on a given day."""

        day_start = date.replace(hour=8, minute=0, second=0, microsecond=0)
        day_end = date.replace(hour=20, minute=0, second=0, microsecond=0)

        existing_lessons = Lesson.objects.filter(
            tutor_id=tutor_id,
            deleted_at__isnull=True,
            status__in=['SCHEDULED', 'ONGOING'],
            start_time__gte=day_start,
            end_time__lte=day_end
        ).order_by('start_time')

        slots = []
        current_time = day_start

        for lesson in existing_lessons:
            gap_minutes = (lesson.start_time - current_time).total_seconds() / 60

            if gap_minutes >= duration_minutes:
                slots.append({
                    'start': current_time,
                    'end': lesson.start_time,
                })

            current_time = lesson.end_time

        # Check remaining time
        remaining_minutes = (day_end - current_time).total_seconds() / 60
        if remaining_minutes >= duration_minutes:
            slots.append({
                'start': current_time,
                'end': day_end,
            })

        return slots
```

---

## DJANGO TEMPLATES

### Calendar Page Template

**File**: `templates/admin_panel/calendar/index.html`

```html
{% extends "admin_panel/base.html" %}
{% load static %}

{% block extra_head %}
<!-- FullCalendar CSS -->
<link href="https://cdn.jsdelivr.net/npm/fullcalendar@6.1.10/index.global.min.css" rel="stylesheet">
<!-- Tippy.js for tooltips -->
<link href="https://unpkg.com/tippy.js@6/themes/light-border.css" rel="stylesheet">
{% endblock %}

{% block content %}
<div x-data="calendarApp()" x-init="init()">
    <!-- Toolbar -->
    <div class="flex items-center justify-between mb-6">
        <div class="flex items-center space-x-4">
            <h1 class="text-2xl font-bold">Kalendarz zajęć</h1>
            <div class="badge badge-secondary" x-text="`Widok: ${currentView}`"></div>
        </div>

        <div class="flex items-center space-x-2">
            <!-- View Switcher -->
            <div class="btn-group">
                <button class="btn btn-sm"
                        :class="currentView === 'timeGridDay' ? 'btn-active' : ''"
                        @click="changeView('timeGridDay')">
                    Dzień
                </button>
                <button class="btn btn-sm"
                        :class="currentView === 'timeGridWeek' ? 'btn-active' : ''"
                        @click="changeView('timeGridWeek')">
                    Tydzień
                </button>
                <button class="btn btn-sm"
                        :class="currentView === 'dayGridMonth' ? 'btn-active' : ''"
                        @click="changeView('dayGridMonth')">
                    Miesiąc
                </button>
                <button class="btn btn-sm"
                        :class="currentView === 'listWeek' ? 'btn-active' : ''"
                        @click="changeView('listWeek')">
                    Lista
                </button>
            </div>

            <!-- Create Button -->
            <button class="btn btn-primary"
                    hx-get="{% url 'lessons:create' %}"
                    hx-target="#modal-content"
                    hx-swap="innerHTML"
                    onclick="document.getElementById('event-modal').showModal()">
                + Nowe zajęcia
            </button>
        </div>
    </div>

    <!-- Calendar Container -->
    <div class="bg-base-100 rounded-lg shadow-sm border p-4">
        <div id="calendar"></div>
    </div>

    <!-- Color Legend -->
    <div class="mt-6 bg-base-100 rounded-lg border p-4">
        <h3 class="font-semibold text-sm mb-3">Legenda kolorów</h3>

        <div class="grid grid-cols-2 gap-4">
            <div>
                <h4 class="text-xs font-medium text-base-content/60 mb-2">Przedmioty</h4>
                <div class="flex flex-wrap gap-2">
                    <span class="badge" style="background-color: #EF4444; color: white;">Matematyka</span>
                    <span class="badge" style="background-color: #3B82F6; color: white;">J. Polski</span>
                    <span class="badge" style="background-color: #10B981; color: white;">J. Angielski</span>
                    <span class="badge" style="background-color: #8B5CF6; color: white;">Fizyka</span>
                    <span class="badge" style="background-color: #F59E0B; color: white;">Chemia</span>
                </div>
            </div>

            <div>
                <h4 class="text-xs font-medium text-base-content/60 mb-2">Status</h4>
                <div class="flex flex-wrap gap-2">
                    <span class="badge" style="background-color: #3B82F6; color: white;">Zaplanowane</span>
                    <span class="badge" style="background-color: #10B981; color: white;">W trakcie</span>
                    <span class="badge" style="background-color: #6B7280; color: white;">Zakończone</span>
                    <span class="badge" style="background-color: #EF4444; color: white;">Anulowane</span>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Event Modal -->
<dialog id="event-modal" class="modal">
    <div class="modal-box max-w-2xl">
        <form method="dialog">
            <button class="btn btn-sm btn-circle btn-ghost absolute right-2 top-2">✕</button>
        </form>
        <div id="modal-content">
            <!-- Content loaded via HTMX -->
            <div class="flex items-center justify-center h-32">
                <span class="loading loading-spinner loading-lg"></span>
            </div>
        </div>
    </div>
    <form method="dialog" class="modal-backdrop">
        <button>close</button>
    </form>
</dialog>

{% csrf_token %}
{% endblock %}

{% block extra_scripts %}
<!-- FullCalendar JS -->
<script src="https://cdn.jsdelivr.net/npm/fullcalendar@6.1.10/index.global.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/@fullcalendar/core@6.1.10/locales/pl.global.min.js"></script>
<!-- Tippy.js -->
<script src="https://unpkg.com/@popperjs/core@2"></script>
<script src="https://unpkg.com/tippy.js@6"></script>
<!-- Calendar Component -->
<script src="{% static 'js/calendar/calendar-component.js' %}"></script>
{% endblock %}
```

### Lesson Form Partial

**File**: `templates/admin_panel/lessons/partials/_lesson_form.html`

```html
<h3 class="font-bold text-lg mb-4">
    {% if lesson %}Edytuj zajęcia{% else %}Nowe zajęcia{% endif %}
</h3>

<form hx-post="{% if lesson %}{% url 'lessons:update' lesson.pk %}{% else %}{% url 'lessons:create' %}{% endif %}"
      hx-target="#modal-content"
      hx-swap="innerHTML"
      class="space-y-4">
    {% csrf_token %}

    <div class="grid grid-cols-2 gap-4">
        <!-- Title -->
        <div class="form-control">
            <label class="label">
                <span class="label-text">Tytuł zajęć *</span>
            </label>
            <input type="text"
                   name="title"
                   value="{{ form.title.value|default:'' }}"
                   class="input input-bordered w-full {% if form.title.errors %}input-error{% endif %}"
                   placeholder="np. Matematyka - funkcje"
                   required>
            {% if form.title.errors %}
                <label class="label">
                    <span class="label-text-alt text-error">{{ form.title.errors.0 }}</span>
                </label>
            {% endif %}
        </div>

        <!-- Color -->
        <div class="form-control">
            <label class="label">
                <span class="label-text">Kolor</span>
            </label>
            <input type="color"
                   name="color"
                   value="{{ form.color.value|default:'#3B82F6' }}"
                   class="input input-bordered h-10 w-20">
        </div>
    </div>

    <!-- Description -->
    <div class="form-control">
        <label class="label">
            <span class="label-text">Opis</span>
        </label>
        <textarea name="description"
                  class="textarea textarea-bordered w-full"
                  rows="2"
                  placeholder="Dodatkowe informacje...">{{ form.description.value|default:'' }}</textarea>
    </div>

    <div class="grid grid-cols-2 gap-4">
        <!-- Subject -->
        <div class="form-control">
            <label class="label">
                <span class="label-text">Przedmiot *</span>
            </label>
            <select name="subject" class="select select-bordered w-full" required>
                <option value="">Wybierz przedmiot</option>
                {% for subject in subjects %}
                    <option value="{{ subject.id }}"
                            {% if form.subject.value == subject.id|stringformat:"s" %}selected{% endif %}>
                        {{ subject.name }}
                    </option>
                {% endfor %}
            </select>
        </div>

        <!-- Level -->
        <div class="form-control">
            <label class="label">
                <span class="label-text">Poziom *</span>
            </label>
            <select name="level" class="select select-bordered w-full" required>
                <option value="">Wybierz poziom</option>
                {% for level in levels %}
                    <option value="{{ level.id }}"
                            {% if form.level.value == level.id|stringformat:"s" %}selected{% endif %}>
                        {{ level.name }}
                    </option>
                {% endfor %}
            </select>
        </div>
    </div>

    <div class="grid grid-cols-2 gap-4">
        <!-- Tutor -->
        <div class="form-control">
            <label class="label">
                <span class="label-text">Korepetytor *</span>
            </label>
            <select name="tutor" class="select select-bordered w-full" required>
                <option value="">Wybierz korepetytora</option>
                {% for tutor in tutors %}
                    <option value="{{ tutor.id }}"
                            {% if form.tutor.value == tutor.id|stringformat:"s" %}selected{% endif %}>
                        {{ tutor.get_full_name }}
                    </option>
                {% endfor %}
            </select>
        </div>

        <!-- Room -->
        <div class="form-control">
            <label class="label">
                <span class="label-text">Sala</span>
            </label>
            <select name="room" class="select select-bordered w-full">
                <option value="">Online / bez sali</option>
                {% for room in rooms %}
                    <option value="{{ room.id }}"
                            {% if form.room.value == room.id|stringformat:"s" %}selected{% endif %}>
                        {{ room.name }} (max {{ room.capacity }} osób)
                    </option>
                {% endfor %}
            </select>
        </div>
    </div>

    <div class="grid grid-cols-2 gap-4">
        <!-- Start Time -->
        <div class="form-control">
            <label class="label">
                <span class="label-text">Rozpoczęcie *</span>
            </label>
            <input type="datetime-local"
                   name="start_time"
                   value="{{ form.start_time.value|date:'Y-m-d\TH:i'|default:initial_start }}"
                   class="input input-bordered w-full"
                   required>
        </div>

        <!-- End Time -->
        <div class="form-control">
            <label class="label">
                <span class="label-text">Zakończenie *</span>
            </label>
            <input type="datetime-local"
                   name="end_time"
                   value="{{ form.end_time.value|date:'Y-m-d\TH:i'|default:initial_end }}"
                   class="input input-bordered w-full"
                   required>
        </div>
    </div>

    <!-- Group Lesson Toggle -->
    <div class="form-control" x-data="{ isGroup: {{ form.is_group_lesson.value|yesno:'true,false' }} }">
        <label class="label cursor-pointer justify-start space-x-3">
            <input type="checkbox"
                   name="is_group_lesson"
                   class="checkbox"
                   x-model="isGroup"
                   {% if form.is_group_lesson.value %}checked{% endif %}>
            <span class="label-text">Zajęcia grupowe</span>
        </label>

        <div x-show="isGroup" x-cloak class="mt-2">
            <label class="label">
                <span class="label-text">Maksymalna liczba uczestników</span>
            </label>
            <input type="number"
                   name="max_participants"
                   value="{{ form.max_participants.value|default:5 }}"
                   min="2"
                   max="20"
                   class="input input-bordered w-full max-w-xs">
        </div>
    </div>

    <!-- Student Selection -->
    <div class="form-control">
        <label class="label">
            <span class="label-text">Uczniowie *</span>
        </label>
        <div class="border rounded-lg p-3 max-h-48 overflow-y-auto">
            {% for student in students %}
                <label class="flex items-center space-x-2 p-1 hover:bg-base-200 rounded cursor-pointer">
                    <input type="checkbox"
                           name="students"
                           value="{{ student.id }}"
                           class="checkbox checkbox-sm"
                           {% if student.id|stringformat:"s" in selected_students %}checked{% endif %}>
                    <span>{{ student.get_full_name }}</span>
                    <span class="text-xs text-base-content/60">
                        ({{ student.student_profile.class_name|default:'N/A' }})
                    </span>
                </label>
            {% endfor %}
        </div>
    </div>

    <!-- Form Actions -->
    <div class="modal-action">
        <button type="button" class="btn btn-ghost" onclick="document.getElementById('event-modal').close()">
            Anuluj
        </button>
        <button type="submit" class="btn btn-primary">
            {% if lesson %}Zapisz{% else %}Utwórz{% endif %}
        </button>
    </div>
</form>
```

---

## RESOURCE CALENDAR VIEW

### Resource View Template

**File**: `templates/admin_panel/calendar/resources.html`

```html
{% extends "admin_panel/base.html" %}
{% load static %}

{% block extra_head %}
<link href="https://cdn.jsdelivr.net/npm/fullcalendar@6.1.10/index.global.min.css" rel="stylesheet">
<link href="https://cdn.jsdelivr.net/npm/@fullcalendar/resource@6.1.10/index.global.min.css" rel="stylesheet">
{% endblock %}

{% block content %}
<div x-data="resourceCalendarApp()" x-init="init()">
    <div class="flex items-center justify-between mb-6">
        <h1 class="text-2xl font-bold">Widok zasobów</h1>

        <!-- Resource Type Switcher -->
        <div class="tabs tabs-boxed">
            <a class="tab" :class="resourceType === 'rooms' ? 'tab-active' : ''"
               @click="switchResourceType('rooms')">
                Sale
            </a>
            <a class="tab" :class="resourceType === 'tutors' ? 'tab-active' : ''"
               @click="switchResourceType('tutors')">
                Korepetytorzy
            </a>
        </div>
    </div>

    <div class="bg-base-100 rounded-lg shadow-sm border p-4">
        <div id="resource-calendar"></div>
    </div>

    <!-- Resource Statistics -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
        <template x-for="resource in resources.slice(0, 3)" :key="resource.id">
            <div class="bg-base-100 p-4 rounded-lg border">
                <h4 class="font-medium" x-text="resource.title"></h4>
                <p class="text-sm text-base-content/60 mt-1" x-text="resource.subtitle"></p>
                <div class="mt-2 text-xs text-base-content/50">
                    <template x-if="resource.extendedProps.type === 'room'">
                        <div>
                            <span>Pojemność: <span x-text="resource.extendedProps.capacity"></span> osób</span>
                        </div>
                    </template>
                    <template x-if="resource.extendedProps.type === 'tutor'">
                        <div>
                            <span>Stawka: <span x-text="resource.extendedProps.hourly_rate"></span> zł/h</span>
                        </div>
                    </template>
                </div>
            </div>
        </template>
    </div>
</div>
{% endblock %}

{% block extra_scripts %}
<script src="https://cdn.jsdelivr.net/npm/fullcalendar@6.1.10/index.global.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/@fullcalendar/resource@6.1.10/index.global.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/@fullcalendar/resource-timegrid@6.1.10/index.global.min.js"></script>

<script>
function resourceCalendarApp() {
    return {
        calendar: null,
        resourceType: 'rooms',
        resources: [],

        init() {
            this.loadResources();
            this.initCalendar();
        },

        async loadResources() {
            const response = await fetch(`/api/calendar/resources/?type=${this.resourceType}`);
            this.resources = await response.json();
        },

        initCalendar() {
            const calendarEl = document.getElementById('resource-calendar');

            this.calendar = new FullCalendar.Calendar(calendarEl, {
                plugins: ['resourceTimeGrid', 'interaction'],
                initialView: 'resourceTimeGridDay',
                locale: 'pl',
                timeZone: 'Europe/Warsaw',
                slotMinTime: '08:00:00',
                slotMaxTime: '20:00:00',
                height: 'auto',

                headerToolbar: {
                    left: 'prev,next today',
                    center: 'title',
                    right: 'resourceTimeGridDay,resourceTimeGridWeek',
                },

                resources: {
                    url: `/api/calendar/resources/?type=${this.resourceType}`,
                },

                events: {
                    url: '/api/calendar/events/',
                    extraParams: {
                        resource_type: this.resourceType,
                    },
                },

                resourceAreaHeaderContent: this.resourceType === 'rooms' ? 'Sale' : 'Korepetytorzy',
                resourceAreaWidth: '200px',
            });

            this.calendar.render();
        },

        switchResourceType(type) {
            this.resourceType = type;
            this.loadResources();
            this.calendar.destroy();
            this.initCalendar();
        },
    };
}
</script>
{% endblock %}
```

---

## URL CONFIGURATION

**File**: `apps/lessons/urls.py`

```python
from django.urls import path
from . import views, api_views

app_name = 'lessons'

urlpatterns = [
    # Calendar views
    path('calendar/', views.CalendarView.as_view(), name='calendar'),
    path('calendar/resources/', views.ResourceCalendarView.as_view(), name='calendar_resources'),

    # Lesson CRUD
    path('', views.LessonListView.as_view(), name='list'),
    path('create/', views.LessonCreateView.as_view(), name='create'),
    path('<uuid:pk>/', views.LessonDetailView.as_view(), name='detail'),
    path('<uuid:pk>/update/', views.LessonUpdateView.as_view(), name='update'),
    path('<uuid:pk>/delete/', views.LessonDeleteView.as_view(), name='delete'),

    # API endpoints
    path('api/events/', api_views.CalendarEventsAPIView.as_view(), name='api_events'),
    path('api/events/<uuid:pk>/move/', api_views.EventMoveAPIView.as_view(), name='api_event_move'),
    path('api/events/<uuid:pk>/resize/', api_views.EventResizeAPIView.as_view(), name='api_event_resize'),
    path('api/resources/', api_views.ResourcesAPIView.as_view(), name='api_resources'),
]
```

---

## COMPLETION CHECKLIST

- [ ] FullCalendar integrated with Django
- [ ] All view types (day/week/month/list) working
- [ ] Drag & drop functionality operational
- [ ] Event creation modal with HTMX functional
- [ ] Conflict detection working
- [ ] Color system applied correctly
- [ ] Resource views displaying properly
- [ ] Polish localization active
- [ ] Mobile responsive design

---

**Next Sprint**: 4.2 - Lesson Management & Student Assignment
