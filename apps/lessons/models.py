from django.conf import settings
from django.db import models

from .managers import LessonManager


class LessonStatus(models.TextChoices):
    SCHEDULED = 'scheduled', 'Zaplanowana'
    ONGOING = 'ongoing', 'W trakcie'
    COMPLETED = 'completed', 'Ukończona'
    CANCELLED = 'cancelled', 'Anulowana'


class AttendanceStatus(models.TextChoices):
    PENDING = 'PENDING', 'Oczekujące'
    PRESENT = 'PRESENT', 'Obecny'
    ABSENT = 'ABSENT', 'Nieobecny'
    LATE = 'LATE', 'Spóźniony'
    EXCUSED = 'EXCUSED', 'Usprawiedliwiony'


class Lesson(models.Model):
    """Lesson/Event model - core of the scheduling system."""

    title = models.CharField('Tytuł', max_length=200)
    description = models.TextField('Opis', blank=True)

    subject = models.ForeignKey(
        'subjects.Subject',
        on_delete=models.PROTECT,
        related_name='lessons',
        verbose_name='Przedmiot',
    )
    level = models.ForeignKey(
        'subjects.Level',
        on_delete=models.PROTECT,
        related_name='lessons',
        verbose_name='Poziom',
    )
    tutor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='tutor_lessons',
        verbose_name='Korepetytor',
        limit_choices_to={'role': 'tutor'},
    )
    room = models.ForeignKey(
        'rooms.Room',
        on_delete=models.SET_NULL,
        related_name='lessons',
        verbose_name='Sala',
        null=True,
        blank=True,
    )

    start_time = models.DateTimeField('Czas rozpoczęcia')
    end_time = models.DateTimeField('Czas zakończenia')

    is_group_lesson = models.BooleanField('Lekcja grupowa', default=False)
    max_participants = models.PositiveIntegerField(
        'Maksymalna liczba uczestników',
        null=True,
        blank=True,
    )
    status = models.CharField(
        'Status',
        max_length=20,
        choices=LessonStatus.choices,
        default=LessonStatus.SCHEDULED,
    )
    notes = models.TextField('Notatki', blank=True)
    color = models.CharField(
        'Kolor',
        max_length=7,
        blank=True,
        help_text='Hex color for calendar display',
    )

    # Recurrence
    is_recurring = models.BooleanField('Cykliczna', default=False)
    recurrence_rule = models.JSONField(
        'Reguła powtarzania',
        null=True,
        blank=True,
    )
    parent_lesson = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        related_name='occurrences',
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField('Utworzono', auto_now_add=True)
    updated_at = models.DateTimeField('Zaktualizowano', auto_now=True)

    objects = LessonManager()

    class Meta:
        db_table = 'lessons'
        verbose_name = 'Lekcja'
        verbose_name_plural = 'Lekcje'
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['start_time']),
            models.Index(fields=['end_time']),
            models.Index(fields=['tutor']),
            models.Index(fields=['room']),
            models.Index(fields=['status']),
            models.Index(fields=['start_time', 'end_time']),
        ]

    def __str__(self):
        return f'{self.title} - {self.start_time.strftime("%Y-%m-%d %H:%M")}'

    @property
    def duration_minutes(self):
        """Get lesson duration in minutes."""
        delta = self.end_time - self.start_time
        return int(delta.total_seconds() / 60)

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError('Czas zakończenia musi być po czasie rozpoczęcia.')

        if self.is_group_lesson and not self.max_participants:
            raise ValidationError(
                'Lekcja grupowa wymaga określenia maksymalnej liczby uczestników.'
            )


class LessonStudent(models.Model):
    """Junction table for lesson-student assignments with attendance."""

    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='lesson_students',
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='student_lessons',
        limit_choices_to={'role': 'student'},
    )

    attendance_status = models.CharField(
        'Status obecności',
        max_length=20,
        choices=AttendanceStatus.choices,
        default=AttendanceStatus.PENDING,
    )
    attendance_marked_at = models.DateTimeField(
        'Czas oznaczenia',
        null=True,
        blank=True,
    )
    attendance_marked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='marked_attendances',
        null=True,
        blank=True,
    )
    attendance_notes = models.TextField('Notatki obecności', blank=True)
    check_in_time = models.DateTimeField(
        'Czas wejścia',
        null=True,
        blank=True,
    )
    check_out_time = models.DateTimeField(
        'Czas wyjścia',
        null=True,
        blank=True,
    )
    notes = models.TextField('Notatki', blank=True)

    created_at = models.DateTimeField('Utworzono', auto_now_add=True)
    updated_at = models.DateTimeField('Zaktualizowano', auto_now=True)

    class Meta:
        db_table = 'lesson_students'
        verbose_name = 'Uczeń na lekcji'
        verbose_name_plural = 'Uczniowie na lekcjach'
        unique_together = ['lesson', 'student']
        indexes = [
            models.Index(fields=['lesson']),
            models.Index(fields=['student']),
            models.Index(fields=['attendance_status']),
        ]

    def __str__(self):
        return f'{self.student.get_full_name()} - {self.lesson.title}'
