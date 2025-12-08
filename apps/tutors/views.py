from datetime import timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

from apps.core.mixins import HTMXMixin, TutorRequiredMixin
from apps.lessons.models import Lesson, LessonStudent

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
        context['recent_students'] = TutorDashboardService.get_my_students(
            tutor, limit=5
        )
        context['today'] = today
        context['week_start'] = week_start
        context['week_end'] = week_end

        return context


class TutorLessonsView(LoginRequiredMixin, TutorRequiredMixin, HTMXMixin, TemplateView):
    """Widok zajec korepetytora."""

    template_name = 'tutor_panel/lessons/list.html'
    partial_template_name = 'tutor_panel/lessons/partials/_lesson_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tutor = self.request.user

        view_type = self.request.GET.get('view', 'calendar')
        context['view_type'] = view_type

        if view_type == 'list':
            context['lessons'] = (
                Lesson.objects.filter(tutor=tutor)
                .select_related('subject', 'room')
                .prefetch_related('lesson_students__student')
                .order_by('-start_time')[:50]
            )

        return context


class TutorCalendarEventsView(LoginRequiredMixin, TutorRequiredMixin, View):
    """API dla kalendarza korepetytora (FullCalendar)."""

    def get(self, request):
        tutor = request.user
        start = request.GET.get('start')
        end = request.GET.get('end')

        lessons = Lesson.objects.filter(
            tutor=tutor,
            start_time__gte=start,
            end_time__lte=end,
        ).select_related('subject', 'room')

        events = []
        for lesson in lessons:
            color = (
                lesson.subject.color
                if lesson.subject and hasattr(lesson.subject, 'color') and lesson.subject.color
                else '#3B82F6'
            )
            if lesson.status == 'completed':
                color = '#22C55E'
            elif lesson.status == 'cancelled':
                color = '#EF4444'

            events.append(
                {
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
                        'students_count': lesson.lesson_students.count(),
                    },
                }
            )

        return JsonResponse(events, safe=False)


class TutorLessonDetailView(LoginRequiredMixin, TutorRequiredMixin, View):
    """Szczegoly zajec dla modala."""

    def get(self, request, lesson_id):
        lesson = get_object_or_404(
            Lesson.objects.select_related('subject', 'room').prefetch_related(
                'lesson_students__student',
            ),
            id=lesson_id,
            tutor=request.user,
        )

        html = render_to_string(
            'tutor_panel/lessons/partials/_lesson_detail_modal.html',
            {'lesson': lesson},
            request=request,
        )

        return HttpResponse(html)


class TutorStudentsView(LoginRequiredMixin, TutorRequiredMixin, HTMXMixin, TemplateView):
    """Lista uczniow korepetytora."""

    template_name = 'tutor_panel/students/list.html'
    partial_template_name = 'tutor_panel/students/partials/_student_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tutor = self.request.user

        search = self.request.GET.get('search', '')
        sort_by = self.request.GET.get('sort', 'name')

        students = TutorDashboardService.get_my_students(tutor)

        # Filtrowanie
        if search:
            search_lower = search.lower()
            students = [
                s
                for s in students
                if search_lower in s['name'].lower()
                or search_lower in s['surname'].lower()
            ]

        # Sortowanie
        if sort_by == 'attendance':
            students.sort(key=lambda x: x['attendance_rate'], reverse=True)
        elif sort_by == 'recent':
            students.sort(
                key=lambda x: x['last_lesson_date'] or timezone.datetime.min.date(),
                reverse=True,
            )

        context['students'] = students

        return context


class TutorStudentDetailView(LoginRequiredMixin, TutorRequiredMixin, TemplateView):
    """Szczegoly ucznia."""

    template_name = 'tutor_panel/students/detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from django.contrib.auth import get_user_model
        from django.http import Http404

        User = get_user_model()

        student_id = kwargs.get('student_id')
        student = get_object_or_404(User, id=student_id)

        tutor = self.request.user

        # Sprawdz czy uczen jest przypisany do tego korepetytora
        is_my_student = LessonStudent.objects.filter(
            lesson__tutor=tutor,
            student=student,
        ).exists()

        if not is_my_student:
            raise Http404('Uczen nie jest Twoim podopiecznym')

        # Statystyki
        context['student'] = student
        context['attendance_stats'] = TutorDashboardService._get_student_attendance_stats(
            tutor, student
        )
        context['lesson_stats'] = TutorDashboardService._get_student_lesson_stats(
            tutor, student
        )

        # Historia zajec
        context['lessons'] = (
            Lesson.objects.filter(
                tutor=tutor,
                lesson_students__student=student,
            )
            .select_related('subject')
            .order_by('-start_time')[:20]
        )

        # Historia obecnosci
        context['attendance_history'] = (
            LessonStudent.objects.filter(
                lesson__tutor=tutor,
                student=student,
            )
            .select_related('lesson', 'lesson__subject')
            .order_by('-lesson__start_time')[:20]
        )

        return context


class TutorQuickAttendanceView(LoginRequiredMixin, TutorRequiredMixin, View):
    """Szybkie oznaczanie obecnosci."""

    def get(self, request, lesson_id):
        """Wyswietla formularz obecnosci."""
        lesson = get_object_or_404(
            Lesson.objects.prefetch_related('lesson_students__student'),
            id=lesson_id,
            tutor=request.user,
        )

        # Pobierz istniejace rekordy obecnosci
        students_data = []
        for ls in lesson.lesson_students.all():
            students_data.append(
                {
                    'id': ls.student.id,
                    'name': ls.student.first_name,
                    'surname': ls.student.last_name,
                    'current_status': ls.attendance_status,
                }
            )

        html = render_to_string(
            'tutor_panel/attendance/partials/_quick_attendance_form.html',
            {
                'lesson': lesson,
                'students': students_data,
            },
            request=request,
        )

        return HttpResponse(html)

    def post(self, request, lesson_id):
        """Zapisuje obecnosc."""
        lesson = get_object_or_404(Lesson, id=lesson_id, tutor=request.user)

        for key, value in request.POST.items():
            if key.startswith('attendance_'):
                student_id = key.replace('attendance_', '')
                status = value

                LessonStudent.objects.filter(
                    lesson=lesson,
                    student_id=student_id,
                ).update(
                    attendance_status=status,
                    attendance_marked_at=timezone.now(),
                    attendance_marked_by=request.user,
                )

        return HttpResponse(status=204, headers={'HX-Trigger': 'attendanceSaved'})


class TutorAttendanceView(LoginRequiredMixin, TutorRequiredMixin, TemplateView):
    """Widok obecnosci korepetytora."""

    template_name = 'tutor_panel/attendance/list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tutor = self.request.user

        # Zajecia wymagajace oznaczenia obecnosci
        today = timezone.now().date()
        pending_lessons = (
            Lesson.objects.filter(
                tutor=tutor,
                start_time__date__lte=today,
                status__in=['scheduled', 'completed'],
                lesson_students__attendance_status='PENDING',
            )
            .distinct()
            .select_related('subject', 'room')
            .prefetch_related('lesson_students__student')
            .order_by('-start_time')[:20]
        )

        context['pending_lessons'] = pending_lessons

        return context


class TutorEarningsView(LoginRequiredMixin, TutorRequiredMixin, TemplateView):
    """Widok zarobkow korepetytora."""

    template_name = 'tutor_panel/earnings/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tutor = self.request.user

        today = timezone.now().date()
        selected_month = self.request.GET.get('month', today.strftime('%Y-%m'))

        context['selected_month'] = selected_month
        context['stats'] = TutorEarningsService.get_earnings_stats(tutor, selected_month)

        # Podzial zarobkow
        year, month = map(int, selected_month.split('-'))
        month_start = timezone.datetime(year, month, 1).date()
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        context['breakdown'] = TutorEarningsService.get_earnings_breakdown(
            tutor, month_start, month_end
        )

        # Ostatnie 12 miesiecy dla selektora
        context['month_options'] = []
        for i in range(12):
            date = today.replace(day=1) - timedelta(days=i * 30)
            context['month_options'].append(
                {
                    'value': date.strftime('%Y-%m'),
                    'label': date.strftime('%B %Y'),
                }
            )

        return context
