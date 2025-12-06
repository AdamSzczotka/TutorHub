from django.db import models
from django.utils import timezone


class LessonQuerySet(models.QuerySet):
    """Custom QuerySet for Lesson model."""

    def upcoming(self):
        """Get upcoming lessons."""
        return self.filter(
            start_time__gte=timezone.now(),
            status='scheduled',
        ).order_by('start_time')

    def past(self):
        """Get past lessons."""
        return self.filter(
            end_time__lt=timezone.now(),
        ).order_by('-start_time')

    def for_tutor(self, user):
        """Get lessons for a specific tutor."""
        return self.filter(tutor=user)

    def for_student(self, user):
        """Get lessons for a specific student."""
        return self.filter(lesson_students__student=user)

    def in_date_range(self, start_date, end_date):
        """Get lessons in a date range."""
        return self.filter(
            start_time__date__gte=start_date,
            start_time__date__lte=end_date,
        )

    def with_attendance(self):
        """Prefetch attendance data."""
        return self.prefetch_related(
            'lesson_students',
            'lesson_students__student',
        )


class LessonManager(models.Manager):
    """Custom Manager for Lesson model."""

    def get_queryset(self):
        return LessonQuerySet(self.model, using=self._db)

    def upcoming(self):
        return self.get_queryset().upcoming()

    def past(self):
        return self.get_queryset().past()

    def for_tutor(self, user):
        return self.get_queryset().for_tutor(user)

    def for_student(self, user):
        return self.get_queryset().for_student(user)

    def in_date_range(self, start_date, end_date):
        return self.get_queryset().in_date_range(start_date, end_date)
