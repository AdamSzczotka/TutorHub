from django.db import models

from apps.core.models import TimeStampedModel


class AttendanceAlert(TimeStampedModel):
    """Model for low attendance alerts."""

    class AlertStatus(models.TextChoices):
        PENDING = 'PENDING', 'Oczekujący'
        RESOLVED = 'RESOLVED', 'Rozwiązany'
        DISMISSED = 'DISMISSED', 'Odrzucony'

    student = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='attendance_alerts',
        verbose_name='Uczeń',
    )
    attendance_rate = models.DecimalField(
        'Frekwencja',
        max_digits=5,
        decimal_places=2,
    )
    threshold = models.PositiveIntegerField(
        'Próg',
        default=80,
    )
    alert_type = models.CharField(
        'Typ alertu',
        max_length=50,
        default='LOW_ATTENDANCE',
    )
    status = models.CharField(
        'Status',
        max_length=20,
        choices=AlertStatus.choices,
        default=AlertStatus.PENDING,
    )
    resolution = models.TextField(
        'Rozwiązanie',
        blank=True,
    )
    resolved_at = models.DateTimeField(
        'Data rozwiązania',
        null=True,
        blank=True,
    )

    class Meta:
        db_table = 'attendance_alerts'
        verbose_name = 'Alert obecności'
        verbose_name_plural = 'Alerty obecności'
        ordering = ['-created_at']

    def __str__(self):
        return f'Alert dla {self.student.get_full_name()} - {self.attendance_rate}%'


class AttendanceReport(TimeStampedModel):
    """Model for monthly attendance reports."""

    student = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='attendance_reports',
        verbose_name='Uczeń',
    )
    month = models.DateField(
        'Miesiąc',
    )
    attendance_rate = models.DecimalField(
        'Frekwencja',
        max_digits=5,
        decimal_places=2,
    )
    total_lessons = models.PositiveIntegerField(
        'Łączna liczba lekcji',
    )
    present_count = models.PositiveIntegerField(
        'Obecny',
    )
    absent_count = models.PositiveIntegerField(
        'Nieobecny',
    )
    late_count = models.PositiveIntegerField(
        'Spóźniony',
    )
    excused_count = models.PositiveIntegerField(
        'Usprawiedliwiony',
    )
    pdf_path = models.CharField(
        'Ścieżka PDF',
        max_length=255,
        blank=True,
    )

    class Meta:
        db_table = 'attendance_reports'
        verbose_name = 'Raport obecności'
        verbose_name_plural = 'Raporty obecności'
        unique_together = ['student', 'month']
        ordering = ['-month']

    def __str__(self):
        return f'Raport dla {self.student.get_full_name()} - {self.month.strftime("%Y-%m")}'
