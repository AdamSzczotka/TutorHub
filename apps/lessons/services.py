from datetime import datetime, timedelta

from django.db.models import Q
from django.utils import timezone

from dateutil.rrule import DAILY, MONTHLY, WEEKLY, rrule

from .models import Lesson, LessonStudent


class CalendarService:
    """Service for calendar operations and conflict detection."""

    def check_conflicts(
        self,
        tutor_id: int,
        start_time: datetime,
        end_time: datetime,
        room_id: int | None = None,
        exclude_lesson_id: int | None = None,
    ) -> list[Lesson]:
        """Check for scheduling conflicts."""
        base_query = Lesson.objects.filter(status__in=['scheduled', 'ongoing'])

        if exclude_lesson_id:
            base_query = base_query.exclude(pk=exclude_lesson_id)

        # Build resource conflict query
        resource_query = Q(tutor_id=tutor_id)
        if room_id:
            resource_query |= Q(room_id=room_id)

        # Time overlap conditions
        time_overlap = Q(start_time__lt=end_time, end_time__gt=start_time)

        conflicts = base_query.filter(resource_query & time_overlap).select_related(
            'subject', 'tutor', 'room'
        )

        return list(conflicts)

    def check_tutor_availability(
        self,
        tutor_id: int,
        start_time: datetime,
        end_time: datetime,
        exclude_lesson_id: int | None = None,
    ) -> bool:
        """Check if tutor is available."""
        conflicts = self.check_conflicts(
            tutor_id=tutor_id,
            start_time=start_time,
            end_time=end_time,
            exclude_lesson_id=exclude_lesson_id,
        )
        return len(conflicts) == 0

    def check_room_availability(
        self,
        room_id: int,
        start_time: datetime,
        end_time: datetime,
        exclude_lesson_id: int | None = None,
    ) -> bool:
        """Check if room is available."""
        conflicts = Lesson.objects.filter(
            room_id=room_id,
            status__in=['scheduled', 'ongoing'],
            start_time__lt=end_time,
            end_time__gt=start_time,
        )

        if exclude_lesson_id:
            conflicts = conflicts.exclude(pk=exclude_lesson_id)

        return not conflicts.exists()

    def check_student_availability(
        self,
        student_id: int,
        start_time: datetime,
        end_time: datetime,
        exclude_lesson_id: int | None = None,
    ) -> bool:
        """Check if student is available."""
        conflicts = Lesson.objects.filter(
            lesson_students__student_id=student_id,
            status__in=['scheduled', 'ongoing'],
            start_time__lt=end_time,
            end_time__gt=start_time,
        )

        if exclude_lesson_id:
            conflicts = conflicts.exclude(pk=exclude_lesson_id)

        return not conflicts.exists()

    def find_available_slots(
        self, tutor_id: int, date: datetime, duration_minutes: int = 60
    ) -> list[dict]:
        """Find available time slots for a tutor on a given day."""
        day_start = date.replace(hour=8, minute=0, second=0, microsecond=0)
        day_end = date.replace(hour=20, minute=0, second=0, microsecond=0)

        existing_lessons = Lesson.objects.filter(
            tutor_id=tutor_id,
            status__in=['scheduled', 'ongoing'],
            start_time__gte=day_start,
            end_time__lte=day_end,
        ).order_by('start_time')

        slots = []
        current_time = day_start

        for lesson in existing_lessons:
            gap_minutes = (lesson.start_time - current_time).total_seconds() / 60

            if gap_minutes >= duration_minutes:
                slots.append(
                    {
                        'start': current_time,
                        'end': lesson.start_time,
                    }
                )

            current_time = lesson.end_time

        # Check remaining time
        remaining_minutes = (day_end - current_time).total_seconds() / 60
        if remaining_minutes >= duration_minutes:
            slots.append(
                {
                    'start': current_time,
                    'end': day_end,
                }
            )

        return slots


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
        end_date: str | None = None,
        days_of_week: list[str] | None = None,
        max_occurrences: int = 90,
    ) -> list[Lesson]:
        """Create recurring lessons based on a pattern."""
        if pattern not in self.PATTERNS:
            raise ValueError(f'Invalid pattern: {pattern}')

        # Parse end date or use default (90 days)
        if end_date:
            until = timezone.datetime.fromisoformat(end_date)
            if timezone.is_naive(until):
                until = timezone.make_aware(until)
        else:
            until = base_lesson.start_time + timedelta(days=90)

        # Calculate duration
        duration = base_lesson.end_time - base_lesson.start_time

        # Convert start_time to naive for rrule (it works better with naive datetimes)
        start_naive = base_lesson.start_time.replace(tzinfo=None)
        until_naive = until.replace(tzinfo=None)

        # Build rule
        rule_kwargs = {
            'freq': self.PATTERNS[pattern],
            'interval': interval,
            'dtstart': start_naive,
            'until': until_naive,
        }

        # Convert days_of_week from strings to integers and filter empty values
        if pattern == 'weekly' and days_of_week:
            weekdays = [int(d) for d in days_of_week if d]
            if weekdays:
                rule_kwargs['byweekday'] = weekdays

        dates = list(rrule(**rule_kwargs))[:max_occurrences]

        # Get original students
        original_students = list(
            base_lesson.lesson_students.values_list('student_id', flat=True)
        )

        created_lessons = []
        calendar_service = CalendarService()

        for date in dates[1:]:  # Skip first (it's the base lesson)
            # Convert naive datetime back to aware
            start_time = timezone.make_aware(date)
            end_time = start_time + duration

            # Check for conflicts
            conflicts = calendar_service.check_conflicts(
                tutor_id=base_lesson.tutor_id,
                room_id=base_lesson.room_id if base_lesson.room_id else None,
                start_time=start_time,
                end_time=end_time,
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
                status='scheduled',
                is_recurring=True,
                parent_lesson=base_lesson,
            )

            # Add students
            for student_id in original_students:
                LessonStudent.objects.create(
                    lesson=lesson,
                    student_id=student_id,
                    attendance_status='unknown',
                )

            created_lessons.append(lesson)

        return created_lessons

    def delete_recurring_series(self, base_lesson: Lesson) -> int:
        """Delete all future lessons in a recurring series."""
        count = Lesson.objects.filter(
            parent_lesson=base_lesson,
            status='scheduled',
            start_time__gt=timezone.now(),
        ).update(status='cancelled')
        return count


class GroupLessonService:
    """Service for managing group lessons."""

    def add_student(self, lesson_id: int, student_id: int) -> dict:
        """Add a student to a group lesson."""
        lesson = (
            Lesson.objects.select_related('room')
            .prefetch_related('lesson_students')
            .get(pk=lesson_id)
        )

        if not lesson.is_group_lesson:
            return {'success': False, 'error': 'To nie są zajęcia grupowe'}

        current_count = lesson.lesson_students.count()

        # Check capacity
        if lesson.max_participants and current_count >= lesson.max_participants:
            return {
                'success': False,
                'error': 'Osiągnięto maksymalną liczbę uczestników',
            }

        # Check room capacity
        if lesson.room and current_count >= lesson.room.capacity:
            return {
                'success': False,
                'error': (
                    f'Sala {lesson.room.name} pomieści '
                    f'maksymalnie {lesson.room.capacity} osób'
                ),
            }

        # Check if already assigned
        if lesson.lesson_students.filter(student_id=student_id).exists():
            return {
                'success': False,
                'error': 'Uczeń jest już przypisany do tych zajęć',
            }

        # Check student availability
        calendar_service = CalendarService()
        if not calendar_service.check_student_availability(
            student_id=student_id,
            start_time=lesson.start_time,
            end_time=lesson.end_time,
            exclude_lesson_id=lesson_id,
        ):
            return {
                'success': False,
                'error': 'Uczeń ma konflikt z innymi zajęciami',
            }

        LessonStudent.objects.create(
            lesson=lesson,
            student_id=student_id,
            attendance_status='unknown',
        )

        return {'success': True}

    def remove_student(self, lesson_id: int, student_id: int) -> dict:
        """Remove a student from a group lesson."""
        deleted, _ = LessonStudent.objects.filter(
            lesson_id=lesson_id,
            student_id=student_id,
        ).delete()

        return {'success': deleted > 0}

    def get_statistics(self, lesson_id: int) -> dict | None:
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
