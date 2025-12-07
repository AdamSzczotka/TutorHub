import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Count
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from apps.accounts.models import User
from apps.core.mixins import AdminRequiredMixin, HTMXMixin
from apps.rooms.models import Room
from apps.subjects.models import Level, Subject

from .forms import LessonForm
from .ical import ICalExporter
from .models import Lesson, LessonStudent
from .services import CalendarService, GroupLessonService, RecurringLessonService


class CalendarView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    """Main calendar view with FullCalendar integration."""

    template_name = 'admin_panel/calendar/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Kalendarz zajęć'
        return context


class ResourceCalendarView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    """Resource-based calendar view (rooms/tutors)."""

    template_name = 'admin_panel/calendar/resources.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Widok zasobów'
        return context


class LessonListView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, ListView):
    """List all lessons with filters."""

    model = Lesson
    template_name = 'admin_panel/lessons/list.html'
    partial_template_name = 'admin_panel/lessons/partials/_lesson_list.html'
    context_object_name = 'lessons'
    paginate_by = 20

    def get_queryset(self):
        queryset = Lesson.objects.select_related(
            'subject', 'level', 'tutor', 'room'
        ).annotate(student_count=Count('lesson_students'))

        # Apply filters
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        tutor_id = self.request.GET.get('tutor')
        if tutor_id:
            queryset = queryset.filter(tutor_id=tutor_id)

        subject_id = self.request.GET.get('subject')
        if subject_id:
            queryset = queryset.filter(subject_id=subject_id)

        return queryset.order_by('-start_time')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Lista zajęć'
        context['tutors'] = User.objects.filter(role='tutor', is_active=True)
        context['subjects'] = Subject.objects.filter(is_active=True)
        context['statuses'] = Lesson.status.field.choices
        return context


class LessonDetailView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, DetailView):
    """View lesson details."""

    model = Lesson
    template_name = 'admin_panel/lessons/detail.html'
    partial_template_name = 'admin_panel/lessons/partials/_lesson_detail.html'
    context_object_name = 'lesson'

    def get_queryset(self):
        return Lesson.objects.select_related(
            'subject', 'level', 'tutor', 'room'
        ).prefetch_related('lesson_students__student')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = self.object.title
        return context


class LessonCreateView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, CreateView):
    """Create a new lesson."""

    model = Lesson
    form_class = LessonForm
    template_name = 'admin_panel/lessons/partials/_lesson_form.html'
    success_url = reverse_lazy('lessons:calendar')

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
        context['form_title'] = 'Nowe zajęcia'
        context['subjects'] = Subject.objects.filter(is_active=True)
        context['levels'] = Level.objects.all().order_by('order_index')
        context['tutors'] = User.objects.filter(role='tutor', is_active=True)
        context['rooms'] = Room.objects.filter(is_active=True)
        students = User.objects.filter(role='student', is_active=True)
        context['students'] = students
        context['students_json'] = json.dumps(
            [
                {
                    'id': s.id,
                    'name': s.get_full_name(),
                    'className': '',
                    'hasConflict': False,
                }
                for s in students
            ]
        )
        context['selected_students_json'] = json.dumps([])
        context['initial_start'] = self.request.GET.get('start', '')
        context['initial_end'] = self.request.GET.get('end', '')
        return context

    @transaction.atomic
    def form_valid(self, form):
        lesson = form.save(commit=False)
        lesson.status = 'scheduled'
        lesson.save()

        # Add students
        students = form.cleaned_data.get('students', [])
        for student in students:
            LessonStudent.objects.create(
                lesson=lesson,
                student=student,
                attendance_status='unknown',
            )

        # Handle recurring lessons
        recurrence_pattern = self.request.POST.get('recurrence_pattern')
        if recurrence_pattern and recurrence_pattern != 'none':
            recurring_service = RecurringLessonService()
            recurring_service.create_recurring_lessons(
                base_lesson=lesson,
                pattern=recurrence_pattern,
                interval=int(self.request.POST.get('recurrence_interval', 1)),
                end_date=self.request.POST.get('recurrence_end_date') or None,
                days_of_week=self.request.POST.getlist('days_of_week'),
            )

        if self.request.htmx:
            return HttpResponse(
                status=204,
                headers={
                    'HX-Trigger': 'eventCreated',
                    'HX-Reswap': 'none',
                },
            )
        return redirect(self.success_url)


class LessonUpdateView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, UpdateView):
    """Update an existing lesson."""

    model = Lesson
    form_class = LessonForm
    template_name = 'admin_panel/lessons/partials/_lesson_form.html'
    success_url = reverse_lazy('lessons:calendar')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Edytuj zajęcia'
        context['lesson'] = self.object
        context['subjects'] = Subject.objects.filter(is_active=True)
        context['levels'] = Level.objects.all().order_by('order_index')
        context['tutors'] = User.objects.filter(role='tutor', is_active=True)
        context['rooms'] = Room.objects.filter(is_active=True)
        students = User.objects.filter(role='student', is_active=True)
        context['students'] = students
        selected_students = list(
            self.object.lesson_students.values_list('student_id', flat=True)
        )
        context['selected_students'] = selected_students
        context['students_json'] = json.dumps(
            [
                {
                    'id': s.id,
                    'name': s.get_full_name(),
                    'className': '',
                    'hasConflict': False,
                }
                for s in students
            ]
        )
        context['selected_students_json'] = json.dumps(selected_students)
        return context

    @transaction.atomic
    def form_valid(self, form):
        lesson = form.save()

        # Update students
        students = form.cleaned_data.get('students', [])
        current_student_ids = set(
            lesson.lesson_students.values_list('student_id', flat=True)
        )
        new_student_ids = {s.id for s in students}

        # Remove students no longer assigned
        lesson.lesson_students.exclude(student_id__in=new_student_ids).delete()

        # Add new students
        for student in students:
            if student.id not in current_student_ids:
                LessonStudent.objects.create(
                    lesson=lesson,
                    student=student,
                    attendance_status='unknown',
                )

        if self.request.htmx:
            return HttpResponse(
                status=204,
                headers={
                    'HX-Trigger': 'eventUpdated',
                    'HX-Reswap': 'none',
                },
            )
        return redirect(self.success_url)


class LessonDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    """Delete (soft cancel) a lesson."""

    model = Lesson
    success_url = reverse_lazy('lessons:calendar')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        # Soft delete - mark as cancelled
        self.object.status = 'cancelled'
        self.object.save()

        if request.htmx:
            return HttpResponse(status=204, headers={'HX-Trigger': 'eventDeleted'})

        return redirect(self.success_url)


class LessonStudentsView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, DetailView):
    """View students assigned to a lesson."""

    model = Lesson
    template_name = 'admin_panel/lessons/partials/_student_assignment.html'
    context_object_name = 'lesson'

    def get_queryset(self):
        return Lesson.objects.prefetch_related('lesson_students__student')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        students = User.objects.filter(role='student', is_active=True)
        context['students'] = students
        selected_students = list(
            self.object.lesson_students.values_list('student_id', flat=True)
        )
        context['students_json'] = json.dumps(
            [
                {
                    'id': s.id,
                    'name': s.get_full_name(),
                    'className': '',
                    'hasConflict': False,
                }
                for s in students
            ]
        )
        context['selected_students_json'] = json.dumps(selected_students)
        context['is_group_lesson'] = self.object.is_group_lesson
        context['max_participants'] = self.object.max_participants or 0
        return context


class AddStudentToLessonView(LoginRequiredMixin, AdminRequiredMixin, View):
    """Add a student to a group lesson."""

    def post(self, request, pk):
        student_id = request.POST.get('student_id')
        if not student_id:
            return JsonResponse({'success': False, 'error': 'Nie podano ucznia'})

        service = GroupLessonService()
        result = service.add_student(lesson_id=pk, student_id=int(student_id))

        if request.htmx:
            if result['success']:
                return HttpResponse(
                    status=204,
                    headers={'HX-Trigger': 'studentAdded'},
                )
            return HttpResponse(result.get('error', 'Błąd'), status=400)

        return JsonResponse(result)


class RemoveStudentFromLessonView(LoginRequiredMixin, AdminRequiredMixin, View):
    """Remove a student from a lesson."""

    def post(self, request, pk, student_pk):
        service = GroupLessonService()
        result = service.remove_student(lesson_id=pk, student_id=student_pk)

        if request.htmx:
            if result['success']:
                return HttpResponse(
                    status=204,
                    headers={'HX-Trigger': 'studentRemoved'},
                )
            return HttpResponse('Błąd usuwania ucznia', status=400)

        return JsonResponse(result)


class CheckStudentAvailabilityView(LoginRequiredMixin, View):
    """API endpoint to check student availability."""

    def post(self, request, pk):
        try:
            data = json.loads(request.body)
            start_time = data.get('start_time')
            end_time = data.get('end_time')

            if not start_time or not end_time:
                return JsonResponse({'available': True})

            from datetime import datetime

            from django.utils import timezone

            start = datetime.fromisoformat(start_time)
            end = datetime.fromisoformat(end_time)

            if timezone.is_naive(start):
                start = timezone.make_aware(start)
            if timezone.is_naive(end):
                end = timezone.make_aware(end)

            service = CalendarService()
            available = service.check_student_availability(
                student_id=pk,
                start_time=start,
                end_time=end,
            )

            return JsonResponse({'available': available})
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({'available': True})


class ICalExportView(LoginRequiredMixin, View):
    """Export user's calendar to iCal format."""

    def get(self, request):
        user = request.user
        exporter = ICalExporter()

        # Get lessons based on user role
        if user.role == 'tutor':
            lessons = Lesson.objects.filter(
                tutor=user,
                status__in=['scheduled', 'ongoing'],
            ).select_related('subject', 'level', 'tutor', 'room')
        elif user.role == 'student':
            lessons = Lesson.objects.filter(
                lesson_students__student=user,
                status__in=['scheduled', 'ongoing'],
            ).select_related('subject', 'level', 'tutor', 'room')
        else:
            lessons = Lesson.objects.filter(
                status__in=['scheduled', 'ongoing'],
            ).select_related('subject', 'level', 'tutor', 'room')

        filename = f'kalendarz-{user.email}.ics'
        return exporter.to_response(lessons, filename)
