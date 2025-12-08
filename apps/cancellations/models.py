from django.conf import settings
from django.db import models
from django.utils import timezone


class CancellationStatus(models.TextChoices):
    PENDING = 'pending', 'Oczekujaca'
    APPROVED = 'approved', 'Zaakceptowana'
    REJECTED = 'rejected', 'Odrzucona'


class MakeupStatus(models.TextChoices):
    PENDING = 'pending', 'Oczekujaca'
    SCHEDULED = 'scheduled', 'Zaplanowana'
    COMPLETED = 'completed', 'Ukonczona'
    EXPIRED = 'expired', 'Wygasla'


class CancellationRequest(models.Model):
    """Model for lesson cancellation requests."""

    lesson = models.ForeignKey(
        'lessons.Lesson',
        on_delete=models.CASCADE,
        related_name='cancellation_requests',
        verbose_name='Lekcja',
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cancellation_requests',
        verbose_name='Uczen',
        limit_choices_to={'role': 'student'},
    )
    reason = models.TextField('Powod')
    status = models.CharField(
        'Status',
        max_length=20,
        choices=CancellationStatus.choices,
        default=CancellationStatus.PENDING,
    )

    request_date = models.DateTimeField('Data zgloszenia', auto_now_add=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_cancellations',
        verbose_name='Rozpatrzone przez',
    )
    reviewed_at = models.DateTimeField('Data rozpatrzenia', null=True, blank=True)
    admin_notes = models.TextField('Notatka administratora', blank=True)

    created_at = models.DateTimeField('Utworzono', auto_now_add=True)
    updated_at = models.DateTimeField('Zaktualizowano', auto_now=True)

    class Meta:
        db_table = 'cancellation_requests'
        verbose_name = 'Prosba o anulowanie'
        verbose_name_plural = 'Prosby o anulowanie'
        ordering = ['-request_date']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['student']),
            models.Index(fields=['lesson']),
            models.Index(fields=['request_date']),
        ]

    def __str__(self):
        return f'Anulowanie: {self.lesson.title} - {self.student.get_full_name()}'

    @property
    def is_pending(self):
        return self.status == CancellationStatus.PENDING

    @property
    def is_approved(self):
        return self.status == CancellationStatus.APPROVED

    @property
    def is_rejected(self):
        return self.status == CancellationStatus.REJECTED


class MakeupLesson(models.Model):
    """Model for makeup lessons (after cancellation approval)."""

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='makeup_lessons',
        verbose_name='Uczen',
        limit_choices_to={'role': 'student'},
    )
    original_lesson = models.ForeignKey(
        'lessons.Lesson',
        on_delete=models.CASCADE,
        related_name='makeup_original',
        verbose_name='Oryginalna lekcja',
    )
    new_lesson = models.ForeignKey(
        'lessons.Lesson',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='makeup_new',
        verbose_name='Nowa lekcja',
    )
    status = models.CharField(
        'Status',
        max_length=20,
        choices=MakeupStatus.choices,
        default=MakeupStatus.PENDING,
    )
    expires_at = models.DateTimeField('Data wygasniecia')
    notes = models.TextField('Notatki', blank=True)

    created_at = models.DateTimeField('Utworzono', auto_now_add=True)
    updated_at = models.DateTimeField('Zaktualizowano', auto_now=True)

    class Meta:
        db_table = 'makeup_lessons'
        verbose_name = 'Zajecia zastepcze'
        verbose_name_plural = 'Zajecia zastepcze'
        ordering = ['expires_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['student']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f'Odrobienie: {self.original_lesson.title} - {self.student.get_full_name()}'

    @property
    def days_remaining(self):
        """Calculate days remaining until expiration."""
        if self.expires_at < timezone.now():
            return 0
        delta = self.expires_at - timezone.now()
        return delta.days

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    @property
    def is_pending(self):
        return self.status == MakeupStatus.PENDING

    @property
    def is_scheduled(self):
        return self.status == MakeupStatus.SCHEDULED

    @property
    def is_completed(self):
        return self.status == MakeupStatus.COMPLETED
