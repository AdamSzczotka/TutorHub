from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.utils import timezone

from apps.lessons.models import Lesson, LessonStudent

User = get_user_model()


class TutorDashboardService:
    """Serwis do obslugi dashboardu korepetytora."""

    @classmethod
    def get_dashboard_stats(cls, tutor):
        """Pobiera statystyki dla dashboardu."""
        today = timezone.now().date()
        month_start = today.replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        # Dzisiejsze zajecia
        today_lessons = Lesson.objects.filter(
            tutor=tutor,
            start_time__date=today,
            status__in=['scheduled', 'ongoing', 'completed'],
        )

        today_count = today_lessons.count()
        today_completed = today_lessons.filter(status='completed').count()

        # Uczniowie
        total_students = (
            LessonStudent.objects.filter(lesson__tutor=tutor)
            .values('student')
            .distinct()
            .count()
        )

        # Godziny w tym miesiacu
        monthly_lessons = Lesson.objects.filter(
            tutor=tutor,
            start_time__date__gte=month_start,
            start_time__date__lte=month_end,
            status='completed',
        )

        monthly_hours = sum(
            (lesson.end_time - lesson.start_time).total_seconds() / 3600
            for lesson in monthly_lessons
        )

        # Zarobki
        monthly_earnings = cls._calculate_monthly_earnings(tutor, month_start, month_end)
        previous_month_start = (month_start - timedelta(days=1)).replace(day=1)
        previous_month_end = month_start - timedelta(days=1)
        previous_earnings = cls._calculate_monthly_earnings(
            tutor, previous_month_start, previous_month_end
        )

        earnings_growth = 0
        if previous_earnings > 0:
            earnings_growth = (
                (monthly_earnings - previous_earnings) / previous_earnings
            ) * 100

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
            status='completed',
        )

        total = Decimal('0.00')
        hourly_rate = (
            tutor.tutor_profile.hourly_rate
            if hasattr(tutor, 'tutor_profile') and tutor.tutor_profile.hourly_rate
            else Decimal('100.00')
        )

        for lesson in completed_lessons:
            hours = (lesson.end_time - lesson.start_time).total_seconds() / 3600
            total += Decimal(str(hours)) * hourly_rate

        return float(total)

    @classmethod
    def get_today_lessons(cls, tutor):
        """Pobiera dzisiejsze zajecia korepetytora."""
        today = timezone.now().date()

        return (
            Lesson.objects.filter(tutor=tutor, start_time__date=today)
            .select_related('subject', 'room')
            .prefetch_related('lesson_students__student')
            .order_by('start_time')
        )

    @classmethod
    def get_week_lessons(cls, tutor, start_date, end_date):
        """Pobiera zajecia na dany tydzien."""
        return (
            Lesson.objects.filter(
                tutor=tutor,
                start_time__date__gte=start_date,
                start_time__date__lte=end_date,
            )
            .select_related('subject', 'room')
            .order_by('start_time')
        )

    @classmethod
    def get_my_students(cls, tutor, limit=None):
        """Pobiera liste uczniow korepetytora."""
        student_ids = (
            LessonStudent.objects.filter(lesson__tutor=tutor)
            .values_list('student_id', flat=True)
            .distinct()
        )

        students = User.objects.filter(id__in=student_ids, is_active=True)

        # Dodaj statystyki
        student_data = []
        for student in students:
            attendance_stats = cls._get_student_attendance_stats(tutor, student)
            lesson_stats = cls._get_student_lesson_stats(tutor, student)

            student_data.append(
                {
                    'id': student.id,
                    'name': student.first_name,
                    'surname': student.last_name,
                    'email': student.email,
                    'avatar': student.avatar.url if student.avatar else None,
                    'attendance_rate': attendance_stats['rate'],
                    'total_lessons': lesson_stats['total'],
                    'upcoming_lessons': lesson_stats['upcoming'],
                    'last_lesson_date': lesson_stats['last_date'],
                }
            )

        # Sortuj po nazwisku
        student_data.sort(key=lambda x: x['surname'])

        if limit:
            student_data = student_data[:limit]

        return student_data

    @classmethod
    def _get_student_attendance_stats(cls, tutor, student):
        """Oblicza statystyki obecnosci ucznia u korepetytora."""
        attendance = LessonStudent.objects.filter(
            lesson__tutor=tutor,
            student=student,
            lesson__status='completed',
        )

        total = attendance.count()
        present = attendance.filter(attendance_status__in=['PRESENT', 'LATE']).count()

        return {
            'rate': round((present / total) * 100, 1) if total > 0 else 0,
            'total': total,
            'present': present,
        }

    @classmethod
    def _get_student_lesson_stats(cls, tutor, student):
        """Oblicza statystyki zajec ucznia u korepetytora."""
        now = timezone.now()

        lessons = LessonStudent.objects.filter(
            lesson__tutor=tutor,
            student=student,
        ).select_related('lesson')

        total = lessons.filter(lesson__status='completed').count()
        upcoming = lessons.filter(
            lesson__status='scheduled',
            lesson__start_time__gt=now,
        ).count()

        last_lesson = (
            lessons.filter(lesson__status='completed')
            .order_by('-lesson__start_time')
            .first()
        )

        return {
            'total': total,
            'upcoming': upcoming,
            'last_date': last_lesson.lesson.start_time.date() if last_lesson else None,
        }


class TutorEarningsService:
    """Serwis do obslugi zarobkow korepetytora."""

    @classmethod
    def get_earnings_stats(cls, tutor, month_year: str):
        """Pobiera statystyki zarobkow za miesiac."""
        year, month = map(int, month_year.split('-'))
        month_start = timezone.datetime(year, month, 1).date()
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        # Poprzedni miesiac
        prev_month_end = month_start - timedelta(days=1)
        prev_month_start = prev_month_end.replace(day=1)

        completed_lessons = Lesson.objects.filter(
            tutor=tutor,
            start_time__date__gte=month_start,
            start_time__date__lte=month_end,
            status='completed',
        )

        prev_lessons = Lesson.objects.filter(
            tutor=tutor,
            start_time__date__gte=prev_month_start,
            start_time__date__lte=prev_month_end,
            status='completed',
        )

        hourly_rate = (
            tutor.tutor_profile.hourly_rate
            if hasattr(tutor, 'tutor_profile') and tutor.tutor_profile.hourly_rate
            else Decimal('100.00')
        )

        # Oblicz godziny
        hours_this_month = sum(
            (lesson.end_time - lesson.start_time).total_seconds() / 3600
            for lesson in completed_lessons
        )

        # Oblicz zarobki
        current_month = float(Decimal(str(hours_this_month)) * hourly_rate)
        prev_hours = sum(
            (lesson.end_time - lesson.start_time).total_seconds() / 3600
            for lesson in prev_lessons
        )
        previous_month = float(Decimal(str(prev_hours)) * hourly_rate)

        # Zajecia indywidualne vs grupowe
        individual = completed_lessons.filter(is_group_lesson=False).count()
        group = completed_lessons.filter(is_group_lesson=True).count()

        # Srednia tygodniowa
        weeks = 4
        avg_hours_per_week = hours_this_month / weeks if hours_this_month > 0 else 0

        return {
            'current_month': current_month,
            'previous_month': previous_month,
            'hours_this_month': round(hours_this_month, 1),
            'avg_hours_per_week': round(avg_hours_per_week, 1),
            'hourly_rate': float(hourly_rate),
            'effective_hourly_rate': (
                current_month / hours_this_month if hours_this_month > 0 else 0
            ),
            'lessons_completed': completed_lessons.count(),
            'lessons_individual': individual,
            'lessons_group': group,
        }

    @classmethod
    def get_earnings_breakdown(cls, tutor, start_date, end_date):
        """Pobiera podzial zarobkow wg przedmiotow."""
        completed_lessons = Lesson.objects.filter(
            tutor=tutor,
            start_time__date__gte=start_date,
            start_time__date__lte=end_date,
            status='completed',
        ).select_related('subject')

        hourly_rate = (
            tutor.tutor_profile.hourly_rate
            if hasattr(tutor, 'tutor_profile') and tutor.tutor_profile.hourly_rate
            else Decimal('100.00')
        )

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

        # Zaokraglij wartosci
        for key in breakdown:
            breakdown[key]['hours'] = round(breakdown[key]['hours'], 1)
            breakdown[key]['amount'] = round(breakdown[key]['amount'], 2)

        return list(breakdown.values())
