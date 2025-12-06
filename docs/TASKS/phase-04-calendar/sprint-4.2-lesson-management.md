# Phase 4 - Sprint 4.2: Lesson Management (Django)

## Tasks 060-066: Lesson CRUD, Student Assignment & Recurring Events

> **Duration**: Week 8 (Second half of Phase 4)
> **Goal**: Complete lesson management system with conflict detection, student assignment, and recurring events
> **Dependencies**: Sprint 4.1 completed (Calendar Integration)

---

## SPRINT OVERVIEW

| Task ID | Description                         | Priority | Dependencies |
| ------- | ----------------------------------- | -------- | ------------ |
| 060     | Lesson CRUD views with HTMX         | Critical | Task 059     |
| 061     | CalendarService conflict detection  | Critical | Task 060     |
| 062     | Student assignment UI               | Critical | Task 061     |
| 063     | Group lessons logic                 | High     | Task 062     |
| 064     | Recurring events system             | High     | Task 063     |
| 065     | Event notifications (Celery)        | High     | Task 064     |
| 066     | iCal export functionality           | Medium   | Task 065     |

---

## LESSON CRUD VIEWS

### Lesson Views

**File**: `apps/lessons/views.py`

```python
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.db import transaction

from apps.core.mixins import AdminRequiredMixin, HTMXMixin
from .models import Lesson, LessonStudent
from .forms import LessonForm
from .services import CalendarService, RecurringLessonService


class CalendarView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    """Main calendar view."""
    template_name = 'admin_panel/calendar/index.html'


class ResourceCalendarView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    """Resource-based calendar view."""
    template_name = 'admin_panel/calendar/resources.html'


class LessonListView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, ListView):
    """List all lessons."""
    model = Lesson
    template_name = 'admin_panel/lessons/list.html'
    partial_template_name = 'admin_panel/lessons/partials/_lesson_list.html'
    context_object_name = 'lessons'
    paginate_by = 20

    def get_queryset(self):
        queryset = Lesson.objects.filter(
            deleted_at__isnull=True
        ).select_related(
            'subject', 'level', 'tutor', 'room'
        ).prefetch_related(
            'lesson_students__student'
        ).order_by('-start_time')

        # Apply filters
        status = self.request.GET.get('status')
        tutor_id = self.request.GET.get('tutor')
        subject_id = self.request.GET.get('subject')
        search = self.request.GET.get('search')

        if status:
            queryset = queryset.filter(status=status)
        if tutor_id:
            queryset = queryset.filter(tutor_id=tutor_id)
        if subject_id:
            queryset = queryset.filter(subject_id=subject_id)
        if search:
            queryset = queryset.filter(title__icontains=search)

        return queryset


class LessonCreateView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, CreateView):
    """Create a new lesson."""
    model = Lesson
    form_class = LessonForm
    template_name = 'admin_panel/lessons/partials/_lesson_form.html'
    success_url = reverse_lazy('lessons:list')

    def get_initial(self):
        initial = super().get_initial()
        # Pre-fill dates from calendar selection
        start = self.request.GET.get('start')
        end = self.request.GET.get('end')
        if start:
            initial['start_time'] = start
        if end:
            initial['end_time'] = end
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['subjects'] = Subject.objects.filter(is_active=True)
        context['levels'] = Level.objects.filter(is_active=True)
        context['tutors'] = User.objects.filter(role='TUTOR', is_active=True)
        context['rooms'] = Room.objects.filter(is_active=True)
        context['students'] = User.objects.filter(role='STUDENT', is_active=True)
        context['initial_start'] = self.request.GET.get('start', '')
        context['initial_end'] = self.request.GET.get('end', '')
        return context

    @transaction.atomic
    def form_valid(self, form):
        lesson = form.save(commit=False)
        lesson.status = 'SCHEDULED'
        lesson.save()

        # Add students
        student_ids = self.request.POST.getlist('students')
        for student_id in student_ids:
            LessonStudent.objects.create(
                lesson=lesson,
                student_id=student_id,
                attendance_status='PENDING'
            )

        # Handle recurring lessons
        recurrence_pattern = self.request.POST.get('recurrence_pattern')
        if recurrence_pattern and recurrence_pattern != 'none':
            recurring_service = RecurringLessonService()
            recurring_service.create_recurring_lessons(
                base_lesson=lesson,
                pattern=recurrence_pattern,
                interval=int(self.request.POST.get('recurrence_interval', 1)),
                end_date=self.request.POST.get('recurrence_end_date'),
                days_of_week=self.request.POST.getlist('days_of_week')
            )

        if self.request.htmx:
            return HttpResponse(
                status=204,
                headers={
                    'HX-Trigger': 'eventCreated',
                    'HX-Reswap': 'none',
                }
            )
        return super().form_valid(form)

    def form_invalid(self, form):
        context = self.get_context_data(form=form)
        return self.render_to_response(context)


class LessonUpdateView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, UpdateView):
    """Update an existing lesson."""
    model = Lesson
    form_class = LessonForm
    template_name = 'admin_panel/lessons/partials/_lesson_form.html'
    success_url = reverse_lazy('lessons:list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lesson'] = self.object
        context['subjects'] = Subject.objects.filter(is_active=True)
        context['levels'] = Level.objects.filter(is_active=True)
        context['tutors'] = User.objects.filter(role='TUTOR', is_active=True)
        context['rooms'] = Room.objects.filter(is_active=True)
        context['students'] = User.objects.filter(role='STUDENT', is_active=True)
        context['selected_students'] = list(
            self.object.lesson_students.values_list('student_id', flat=True)
        )
        return context

    @transaction.atomic
    def form_valid(self, form):
        lesson = form.save()

        # Update students
        student_ids = self.request.POST.getlist('students')
        LessonStudent.objects.filter(lesson=lesson).delete()
        for student_id in student_ids:
            LessonStudent.objects.create(
                lesson=lesson,
                student_id=student_id,
                attendance_status='PENDING'
            )

        if self.request.htmx:
            return HttpResponse(
                status=204,
                headers={
                    'HX-Trigger': 'eventUpdated',
                    'HX-Reswap': 'none',
                }
            )
        return super().form_valid(form)


class LessonDetailView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, DetailView):
    """View lesson details."""
    model = Lesson
    template_name = 'admin_panel/lessons/partials/_lesson_detail.html'
    context_object_name = 'lesson'

    def get_queryset(self):
        return Lesson.objects.select_related(
            'subject', 'level', 'tutor', 'room'
        ).prefetch_related('lesson_students__student')


class LessonDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    """Delete (soft) a lesson."""
    model = Lesson
    success_url = reverse_lazy('lessons:list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        # Soft delete
        self.object.deleted_at = timezone.now()
        self.object.status = 'CANCELLED'
        self.object.save()

        if request.htmx:
            return HttpResponse(
                status=204,
                headers={'HX-Trigger': 'eventDeleted'}
            )

        return redirect(self.success_url)
```

### Lesson Form

**File**: `apps/lessons/forms.py`

```python
from django import forms
from django.core.exceptions import ValidationError
from .models import Lesson
from .services import CalendarService


class LessonForm(forms.ModelForm):
    """Form for creating/editing lessons."""

    class Meta:
        model = Lesson
        fields = [
            'title', 'description', 'subject', 'level', 'tutor',
            'room', 'start_time', 'end_time', 'is_group_lesson',
            'max_participants', 'color'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'np. Matematyka - funkcje'
            }),
            'description': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 2,
                'placeholder': 'Dodatkowe informacje...'
            }),
            'subject': forms.Select(attrs={
                'class': 'select select-bordered w-full'
            }),
            'level': forms.Select(attrs={
                'class': 'select select-bordered w-full'
            }),
            'tutor': forms.Select(attrs={
                'class': 'select select-bordered w-full'
            }),
            'room': forms.Select(attrs={
                'class': 'select select-bordered w-full'
            }),
            'start_time': forms.DateTimeInput(attrs={
                'class': 'input input-bordered w-full',
                'type': 'datetime-local'
            }),
            'end_time': forms.DateTimeInput(attrs={
                'class': 'input input-bordered w-full',
                'type': 'datetime-local'
            }),
            'is_group_lesson': forms.CheckboxInput(attrs={
                'class': 'checkbox'
            }),
            'max_participants': forms.NumberInput(attrs={
                'class': 'input input-bordered w-full max-w-xs',
                'min': 2,
                'max': 20
            }),
            'color': forms.TextInput(attrs={
                'class': 'input input-bordered h-10 w-20',
                'type': 'color'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        tutor = cleaned_data.get('tutor')
        room = cleaned_data.get('room')
        is_group_lesson = cleaned_data.get('is_group_lesson')
        max_participants = cleaned_data.get('max_participants')

        # Validate time range
        if start_time and end_time:
            if end_time <= start_time:
                raise ValidationError({
                    'end_time': 'Czas zakończenia musi być późniejszy niż rozpoczęcia'
                })

        # Validate group lesson settings
        if is_group_lesson and not max_participants:
            raise ValidationError({
                'max_participants': 'Podaj maksymalną liczbę uczestników dla zajęć grupowych'
            })

        # Check for conflicts
        if start_time and end_time and tutor:
            calendar_service = CalendarService()
            exclude_id = self.instance.pk if self.instance else None

            conflicts = calendar_service.check_conflicts(
                tutor_id=str(tutor.id),
                room_id=str(room.id) if room else None,
                start_time=start_time,
                end_time=end_time,
                exclude_lesson_id=exclude_id
            )

            if conflicts:
                conflict_titles = [c.title for c in conflicts]
                raise ValidationError(
                    f'Konflikt z zajęciami: {", ".join(conflict_titles)}'
                )

        return cleaned_data
```

---

## RECURRING LESSONS SERVICE

**File**: `apps/lessons/services.py` (add to existing)

```python
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from dateutil.rrule import rrule, DAILY, WEEKLY, MONTHLY
from typing import List, Optional
from django.utils import timezone

from .models import Lesson, LessonStudent


class RecurringLessonService:
    """Service for creating recurring lessons."""

    PATTERNS = {
        'daily': DAILY,
        'weekly': WEEKLY,
        'monthly': MONTHLY,
    }

    def create_recurring_lessons(
        self,
        base_lesson: Lesson,
        pattern: str,
        interval: int = 1,
        end_date: Optional[str] = None,
        days_of_week: Optional[List[int]] = None,
        max_occurrences: int = 90
    ) -> List[Lesson]:
        """Create recurring lessons based on a pattern."""

        if pattern not in self.PATTERNS:
            raise ValueError(f'Invalid pattern: {pattern}')

        # Parse end date or use default (90 days)
        if end_date:
            until = timezone.datetime.fromisoformat(end_date)
        else:
            until = base_lesson.start_time + timedelta(days=90)

        # Calculate duration
        duration = base_lesson.end_time - base_lesson.start_time

        # Build rule
        rule_kwargs = {
            'freq': self.PATTERNS[pattern],
            'interval': interval,
            'dtstart': base_lesson.start_time,
            'until': until,
            'count': max_occurrences,
        }

        if pattern == 'weekly' and days_of_week:
            rule_kwargs['byweekday'] = [int(d) for d in days_of_week]

        dates = list(rrule(**rule_kwargs))

        # Get original students
        original_students = list(
            base_lesson.lesson_students.values_list('student_id', flat=True)
        )

        created_lessons = []
        calendar_service = CalendarService()

        for date in dates[1:]:  # Skip first (it's the base lesson)
            start_time = date
            end_time = date + duration

            # Check for conflicts
            conflicts = calendar_service.check_conflicts(
                tutor_id=str(base_lesson.tutor_id),
                room_id=str(base_lesson.room_id) if base_lesson.room_id else None,
                start_time=start_time,
                end_time=end_time
            )

            if conflicts:
                continue  # Skip conflicting dates

            # Create lesson
            lesson = Lesson.objects.create(
                title=base_lesson.title,
                description=base_lesson.description,
                subject=base_lesson.subject,
                level=base_lesson.level,
                tutor=base_lesson.tutor,
                room=base_lesson.room,
                start_time=start_time,
                end_time=end_time,
                is_group_lesson=base_lesson.is_group_lesson,
                max_participants=base_lesson.max_participants,
                color=base_lesson.color,
                status='SCHEDULED',
                parent_lesson=base_lesson,  # Link to original
            )

            # Add students
            for student_id in original_students:
                LessonStudent.objects.create(
                    lesson=lesson,
                    student_id=student_id,
                    attendance_status='PENDING'
                )

            created_lessons.append(lesson)

        return created_lessons

    def delete_recurring_series(self, base_lesson: Lesson) -> int:
        """Delete all lessons in a recurring series."""
        count = Lesson.objects.filter(
            parent_lesson=base_lesson,
            status='SCHEDULED',
            start_time__gt=timezone.now()
        ).update(
            deleted_at=timezone.now(),
            status='CANCELLED'
        )
        return count
```

---

## GROUP LESSONS SERVICE

**File**: `apps/lessons/services.py` (add to existing)

```python
class GroupLessonService:
    """Service for managing group lessons."""

    def add_student(self, lesson_id: str, student_id: str) -> dict:
        """Add a student to a group lesson."""
        lesson = Lesson.objects.select_related('room').prefetch_related(
            'lesson_students'
        ).get(pk=lesson_id)

        if not lesson.is_group_lesson:
            return {'success': False, 'error': 'To nie są zajęcia grupowe'}

        current_count = lesson.lesson_students.count()

        # Check capacity
        if lesson.max_participants and current_count >= lesson.max_participants:
            return {'success': False, 'error': 'Osiągnięto maksymalną liczbę uczestników'}

        # Check room capacity
        if lesson.room and current_count >= lesson.room.capacity:
            return {
                'success': False,
                'error': f'Sala {lesson.room.name} pomieści maksymalnie {lesson.room.capacity} osób'
            }

        # Check if already assigned
        if lesson.lesson_students.filter(student_id=student_id).exists():
            return {'success': False, 'error': 'Uczeń jest już przypisany do tych zajęć'}

        # Check student availability
        calendar_service = CalendarService()
        if not calendar_service.check_student_availability(
            student_id=student_id,
            start_time=lesson.start_time,
            end_time=lesson.end_time,
            exclude_lesson_id=lesson_id
        ):
            return {'success': False, 'error': 'Uczeń ma konflikt z innymi zajęciami'}

        LessonStudent.objects.create(
            lesson=lesson,
            student_id=student_id,
            attendance_status='PENDING'
        )

        return {'success': True}

    def remove_student(self, lesson_id: str, student_id: str) -> dict:
        """Remove a student from a group lesson."""
        deleted, _ = LessonStudent.objects.filter(
            lesson_id=lesson_id,
            student_id=student_id
        ).delete()

        return {'success': deleted > 0}

    def get_statistics(self, lesson_id: str) -> dict:
        """Get statistics for a group lesson."""
        lesson = Lesson.objects.prefetch_related('lesson_students').get(pk=lesson_id)

        if not lesson.is_group_lesson:
            return None

        current = lesson.lesson_students.count()
        max_p = lesson.max_participants or 0
        available = max(0, max_p - current)
        utilization = (current / max_p * 100) if max_p > 0 else 0

        return {
            'current_participants': current,
            'max_participants': max_p,
            'available_slots': available,
            'utilization_rate': round(utilization, 1),
            'is_full': current >= max_p if max_p > 0 else False,
        }
```

---

## STUDENT ASSIGNMENT TEMPLATE

**File**: `templates/admin_panel/lessons/partials/_student_assignment.html`

```html
<div class="space-y-4" x-data="studentAssignment()">
    <div class="flex items-center justify-between">
        <label class="label">
            <span class="label-text font-medium">Przypisani uczniowie *</span>
        </label>
        <div class="badge" :class="isFull ? 'badge-error' : 'badge-secondary'">
            <span x-text="selectedCount"></span>
            <template x-if="isGroupLesson && maxParticipants">
                <span> / <span x-text="maxParticipants"></span></span>
            </template>
        </div>
    </div>

    <!-- Search Input -->
    <div class="form-control">
        <input type="text"
               x-model="searchQuery"
               class="input input-bordered w-full"
               placeholder="Szukaj ucznia...">
    </div>

    <!-- Student List -->
    <div class="border rounded-lg max-h-64 overflow-y-auto">
        <template x-for="student in filteredStudents" :key="student.id">
            <label class="flex items-center justify-between p-3 hover:bg-base-200 cursor-pointer border-b last:border-b-0"
                   :class="{ 'bg-error/10': student.hasConflict }">
                <div class="flex items-center space-x-3">
                    <input type="checkbox"
                           name="students"
                           :value="student.id"
                           :checked="isSelected(student.id)"
                           :disabled="!isSelected(student.id) && isFull"
                           @change="toggleStudent(student.id)"
                           class="checkbox checkbox-sm">
                    <div>
                        <div class="font-medium" x-text="student.name"></div>
                        <div class="text-xs text-base-content/60" x-text="student.className"></div>
                    </div>
                </div>
                <template x-if="student.hasConflict">
                    <span class="badge badge-warning badge-sm">Konflikt</span>
                </template>
            </label>
        </template>
    </div>

    <!-- Selected Students Display -->
    <template x-if="selectedStudents.length > 0">
        <div class="flex flex-wrap gap-2">
            <template x-for="student in selectedStudents" :key="student.id">
                <span class="badge badge-lg gap-1"
                      :class="student.hasConflict ? 'badge-warning' : 'badge-primary'">
                    <span x-text="student.name"></span>
                    <button type="button" @click="toggleStudent(student.id)" class="hover:text-error">
                        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                        </svg>
                    </button>
                </span>
            </template>
        </div>
    </template>

    <!-- Conflict Warning -->
    <template x-if="conflictCount > 0">
        <div class="alert alert-warning">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
            </svg>
            <span x-text="`${conflictCount} uczeń(ów) ma konflikt z innymi zajęciami`"></span>
        </div>
    </template>
</div>

<script>
function studentAssignment() {
    return {
        students: {{ students_json|safe }},
        selectedIds: {{ selected_students_json|safe }},
        isGroupLesson: {{ is_group_lesson|yesno:'true,false' }},
        maxParticipants: {{ max_participants|default:0 }},
        searchQuery: '',
        conflicts: [],

        get selectedCount() {
            return this.selectedIds.length;
        },

        get isFull() {
            if (!this.isGroupLesson || !this.maxParticipants) return false;
            return this.selectedIds.length >= this.maxParticipants;
        },

        get filteredStudents() {
            if (!this.searchQuery) return this.students;
            const query = this.searchQuery.toLowerCase();
            return this.students.filter(s =>
                s.name.toLowerCase().includes(query)
            );
        },

        get selectedStudents() {
            return this.students.filter(s => this.selectedIds.includes(s.id));
        },

        get conflictCount() {
            return this.selectedStudents.filter(s => s.hasConflict).length;
        },

        isSelected(id) {
            return this.selectedIds.includes(id);
        },

        toggleStudent(id) {
            const index = this.selectedIds.indexOf(id);
            if (index > -1) {
                this.selectedIds.splice(index, 1);
            } else if (!this.isFull) {
                this.selectedIds.push(id);
            }
        },

        async checkConflicts() {
            // Check conflicts via API when times change
            const startTime = document.querySelector('[name="start_time"]')?.value;
            const endTime = document.querySelector('[name="end_time"]')?.value;

            if (!startTime || !endTime) return;

            for (const id of this.selectedIds) {
                const response = await fetch(`/api/students/${id}/check-availability/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                    },
                    body: JSON.stringify({ start_time: startTime, end_time: endTime })
                });
                const data = await response.json();
                const student = this.students.find(s => s.id === id);
                if (student) {
                    student.hasConflict = !data.available;
                }
            }
        },

        init() {
            // Watch for time changes
            const startInput = document.querySelector('[name="start_time"]');
            const endInput = document.querySelector('[name="end_time"]');

            if (startInput) startInput.addEventListener('change', () => this.checkConflicts());
            if (endInput) endInput.addEventListener('change', () => this.checkConflicts());
        }
    };
}
</script>
```

---

## RECURRENCE EDITOR

**File**: `templates/admin_panel/lessons/partials/_recurrence_editor.html`

```html
<div class="bg-base-200 rounded-lg p-4 space-y-4" x-data="recurrenceEditor()">
    <!-- Toggle -->
    <div class="flex items-center justify-between">
        <div class="flex items-center space-x-2">
            <svg class="w-5 h-5 text-base-content/60" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
            </svg>
            <label class="label-text font-medium">Zajęcia cykliczne</label>
        </div>
        <input type="checkbox" x-model="enabled" class="toggle">
    </div>

    <!-- Recurrence Settings -->
    <div x-show="enabled" x-cloak class="space-y-4">
        <div class="grid grid-cols-2 gap-4">
            <!-- Pattern -->
            <div class="form-control">
                <label class="label">
                    <span class="label-text">Wzorzec powtarzania</span>
                </label>
                <select name="recurrence_pattern" x-model="pattern" class="select select-bordered w-full">
                    <option value="none">Bez powtarzania</option>
                    <option value="daily">Codziennie</option>
                    <option value="weekly">Co tydzień</option>
                    <option value="monthly">Co miesiąc</option>
                </select>
            </div>

            <!-- Interval -->
            <div class="form-control">
                <label class="label">
                    <span class="label-text">Interwał</span>
                </label>
                <input type="number"
                       name="recurrence_interval"
                       x-model="interval"
                       min="1"
                       max="30"
                       class="input input-bordered w-full">
                <label class="label">
                    <span class="label-text-alt" x-text="intervalDescription"></span>
                </label>
            </div>
        </div>

        <!-- Days of Week (for weekly) -->
        <div x-show="pattern === 'weekly'" class="form-control">
            <label class="label">
                <span class="label-text">Dni tygodnia</span>
            </label>
            <div class="flex flex-wrap gap-2">
                <template x-for="day in daysOfWeek" :key="day.value">
                    <label class="cursor-pointer">
                        <input type="checkbox"
                               name="days_of_week"
                               :value="day.value"
                               :checked="selectedDays.includes(day.value)"
                               @change="toggleDay(day.value)"
                               class="hidden">
                        <span class="badge badge-lg"
                              :class="selectedDays.includes(day.value) ? 'badge-primary' : 'badge-outline'"
                              x-text="day.label">
                        </span>
                    </label>
                </template>
            </div>
        </div>

        <!-- End Date -->
        <div class="form-control">
            <label class="label">
                <span class="label-text">Data zakończenia (opcjonalne)</span>
            </label>
            <input type="date"
                   name="recurrence_end_date"
                   x-model="endDate"
                   :min="minEndDate"
                   class="input input-bordered w-full">
            <label class="label">
                <span class="label-text-alt">Pozostaw puste dla 90 dni domyślnie</span>
            </label>
        </div>

        <!-- Preview -->
        <div x-show="pattern !== 'none'" class="alert alert-info">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
            <span x-text="previewText"></span>
        </div>
    </div>
</div>

<script>
function recurrenceEditor() {
    return {
        enabled: false,
        pattern: 'weekly',
        interval: 1,
        endDate: '',
        selectedDays: [1, 2, 3, 4, 5], // Mon-Fri default

        daysOfWeek: [
            { value: 0, label: 'Pn' },
            { value: 1, label: 'Wt' },
            { value: 2, label: 'Śr' },
            { value: 3, label: 'Cz' },
            { value: 4, label: 'Pt' },
            { value: 5, label: 'Sb' },
            { value: 6, label: 'Nd' },
        ],

        get minEndDate() {
            const today = new Date();
            return today.toISOString().split('T')[0];
        },

        get intervalDescription() {
            const patterns = {
                daily: ['dzień', 'dni'],
                weekly: ['tydzień', 'tygodnie'],
                monthly: ['miesiąc', 'miesiące'],
            };
            const [singular, plural] = patterns[this.pattern] || ['', ''];
            return `Co ${this.interval} ${this.interval === 1 ? singular : plural}`;
        },

        get previewText() {
            if (this.pattern === 'none') return '';

            let text = `Zajęcia będą powtarzane ${this.intervalDescription.toLowerCase()}`;

            if (this.pattern === 'weekly' && this.selectedDays.length > 0) {
                const dayNames = this.selectedDays.map(d =>
                    this.daysOfWeek.find(day => day.value === d)?.label
                ).join(', ');
                text += ` w dni: ${dayNames}`;
            }

            if (this.endDate) {
                text += ` do ${this.endDate}`;
            } else {
                text += ' (przez 90 dni)';
            }

            return text;
        },

        toggleDay(value) {
            const index = this.selectedDays.indexOf(value);
            if (index > -1) {
                this.selectedDays.splice(index, 1);
            } else {
                this.selectedDays.push(value);
                this.selectedDays.sort();
            }
        },
    };
}
</script>
```

---

## NOTIFICATION SERVICE (CELERY)

**File**: `apps/lessons/tasks.py`

```python
from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from datetime import timedelta

from .models import Lesson


@shared_task
def send_lesson_reminders():
    """Send reminder emails 24h before lessons."""
    tomorrow = timezone.now() + timedelta(days=1)
    tomorrow_start = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow_end = tomorrow.replace(hour=23, minute=59, second=59, microsecond=999999)

    lessons = Lesson.objects.filter(
        start_time__gte=tomorrow_start,
        start_time__lte=tomorrow_end,
        status='SCHEDULED',
        deleted_at__isnull=True
    ).select_related(
        'subject', 'level', 'tutor', 'room'
    ).prefetch_related('lesson_students__student')

    for lesson in lessons:
        # Send to tutor
        send_lesson_reminder_email.delay(
            lesson_id=str(lesson.id),
            recipient_id=str(lesson.tutor_id),
            recipient_type='tutor'
        )

        # Send to students
        for ls in lesson.lesson_students.all():
            send_lesson_reminder_email.delay(
                lesson_id=str(lesson.id),
                recipient_id=str(ls.student_id),
                recipient_type='student'
            )


@shared_task
def send_lesson_reminder_email(lesson_id: str, recipient_id: str, recipient_type: str):
    """Send individual reminder email."""
    from apps.accounts.models import User

    lesson = Lesson.objects.select_related(
        'subject', 'level', 'tutor', 'room'
    ).get(pk=lesson_id)

    recipient = User.objects.get(pk=recipient_id)

    context = {
        'lesson': lesson,
        'recipient': recipient,
        'recipient_type': recipient_type,
    }

    subject = f'Przypomnienie: Zajęcia jutro - {lesson.title}'
    html_message = render_to_string('emails/lesson_reminder.html', context)
    plain_message = render_to_string('emails/lesson_reminder.txt', context)

    send_mail(
        subject=subject,
        message=plain_message,
        html_message=html_message,
        from_email=None,  # Uses DEFAULT_FROM_EMAIL
        recipient_list=[recipient.email],
        fail_silently=False,
    )


@shared_task
def send_lesson_created_notification(lesson_id: str):
    """Notify participants about new lesson."""
    lesson = Lesson.objects.select_related(
        'subject', 'level', 'tutor', 'room'
    ).prefetch_related('lesson_students__student').get(pk=lesson_id)

    recipients = [lesson.tutor.email]
    for ls in lesson.lesson_students.all():
        recipients.append(ls.student.email)

    context = {'lesson': lesson}
    subject = f'Nowe zajęcia: {lesson.title}'
    html_message = render_to_string('emails/lesson_created.html', context)

    for email in recipients:
        send_mail(
            subject=subject,
            message='',
            html_message=html_message,
            from_email=None,
            recipient_list=[email],
            fail_silently=True,
        )


@shared_task
def send_lesson_cancelled_notification(lesson_id: str, reason: str = ''):
    """Notify participants about cancelled lesson."""
    lesson = Lesson.objects.select_related(
        'subject', 'level', 'tutor', 'room'
    ).prefetch_related('lesson_students__student').get(pk=lesson_id)

    recipients = [lesson.tutor.email]
    for ls in lesson.lesson_students.all():
        recipients.append(ls.student.email)

    context = {'lesson': lesson, 'reason': reason}
    subject = f'Odwołane zajęcia: {lesson.title}'
    html_message = render_to_string('emails/lesson_cancelled.html', context)

    for email in recipients:
        send_mail(
            subject=subject,
            message='',
            html_message=html_message,
            from_email=None,
            recipient_list=[email],
            fail_silently=True,
        )
```

### Celery Beat Schedule

**File**: `napiatke/celery.py` (add schedule)

```python
from celery.schedules import crontab

app.conf.beat_schedule = {
    'send-lesson-reminders': {
        'task': 'apps.lessons.tasks.send_lesson_reminders',
        'schedule': crontab(hour=18, minute=0),  # Daily at 6 PM
    },
}
```

---

## ICAL EXPORT

**File**: `apps/lessons/ical.py`

```python
from icalendar import Calendar, Event
from django.http import HttpResponse
from django.utils import timezone
from datetime import datetime
import uuid


class ICalExporter:
    """Export lessons to iCal format."""

    def generate_calendar(self, lessons, calendar_name: str = 'Zajęcia - Na Piątkę') -> Calendar:
        """Generate iCal calendar from lessons."""
        cal = Calendar()
        cal.add('prodid', '-//Na Piątkę//Tutoring CMS//PL')
        cal.add('version', '2.0')
        cal.add('calscale', 'GREGORIAN')
        cal.add('x-wr-calname', calendar_name)
        cal.add('x-wr-timezone', 'Europe/Warsaw')

        for lesson in lessons:
            event = Event()
            event.add('uid', f'{lesson.id}@napiatke.pl')
            event.add('summary', lesson.title)
            event.add('dtstart', lesson.start_time)
            event.add('dtend', lesson.end_time)
            event.add('dtstamp', timezone.now())

            # Description
            description_parts = []
            if lesson.description:
                description_parts.append(lesson.description)
            if lesson.subject:
                description_parts.append(f'Przedmiot: {lesson.subject.name}')
            if lesson.level:
                description_parts.append(f'Poziom: {lesson.level.name}')
            if lesson.tutor:
                description_parts.append(f'Korepetytor: {lesson.tutor.get_full_name()}')

            event.add('description', '\n'.join(description_parts))

            # Location
            if lesson.room:
                event.add('location', lesson.room.name)
            else:
                event.add('location', 'Online')

            # Status
            if lesson.status == 'CANCELLED':
                event.add('status', 'CANCELLED')
            else:
                event.add('status', 'CONFIRMED')

            # Organizer
            if lesson.tutor:
                event.add('organizer', f'mailto:{lesson.tutor.email}')

            cal.add_component(event)

        return cal

    def to_response(self, lessons, filename: str = 'calendar.ics') -> HttpResponse:
        """Generate HTTP response with iCal file."""
        cal = self.generate_calendar(lessons)

        response = HttpResponse(
            cal.to_ical(),
            content_type='text/calendar'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        return response
```

### iCal View

**File**: `apps/lessons/views.py` (add)

```python
from django.views import View
from .ical import ICalExporter


class ICalExportView(LoginRequiredMixin, View):
    """Export user's calendar to iCal format."""

    def get(self, request):
        user = request.user
        exporter = ICalExporter()

        # Get lessons based on user role
        if user.role == 'TUTOR':
            lessons = Lesson.objects.filter(
                tutor=user,
                deleted_at__isnull=True
            ).select_related('subject', 'level', 'tutor', 'room')
        elif user.role == 'STUDENT':
            lessons = Lesson.objects.filter(
                lesson_students__student=user,
                deleted_at__isnull=True
            ).select_related('subject', 'level', 'tutor', 'room')
        else:
            lessons = Lesson.objects.filter(
                deleted_at__isnull=True
            ).select_related('subject', 'level', 'tutor', 'room')

        filename = f'kalendarz-{user.email}.ics'
        return exporter.to_response(lessons, filename)
```

---

## URL CONFIGURATION UPDATE

**File**: `apps/lessons/urls.py` (update)

```python
urlpatterns = [
    # ... existing urls ...

    # iCal export
    path('export/ical/', views.ICalExportView.as_view(), name='export_ical'),

    # Group lesson management
    path('<uuid:pk>/students/', views.LessonStudentsView.as_view(), name='students'),
    path('<uuid:pk>/students/add/', views.AddStudentToLessonView.as_view(), name='add_student'),
    path('<uuid:pk>/students/<uuid:student_pk>/remove/', views.RemoveStudentFromLessonView.as_view(), name='remove_student'),
]
```

---

## COMPLETION CHECKLIST

- [ ] Lesson CRUD with HTMX working
- [ ] Form validation with conflict detection
- [ ] Student assignment UI operational
- [ ] Group lesson capacity limits enforced
- [ ] Recurring events creation functional
- [ ] Celery tasks for notifications
- [ ] Email reminders sending correctly
- [ ] iCal export working
- [ ] All validations comprehensive

---

**Next Sprint**: 5.1 - Attendance Marking System
