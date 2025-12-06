from django.conf import settings
from django.db import models


class NotificationType(models.TextChoices):
    LESSON_REMINDER = 'lesson_reminder', 'Przypomnienie o lekcji'
    LESSON_CANCELLED = 'lesson_cancelled', 'Lekcja anulowana'
    LESSON_RESCHEDULED = 'lesson_rescheduled', 'Lekcja przełożona'
    NEW_MESSAGE = 'new_message', 'Nowa wiadomość'
    INVOICE_GENERATED = 'invoice_generated', 'Faktura wygenerowana'
    ATTENDANCE_MARKED = 'attendance_marked', 'Obecność oznaczona'
    SYSTEM = 'system', 'Systemowe'


class Notification(models.Model):
    """User notification system."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    type = models.CharField(
        'Typ',
        max_length=30,
        choices=NotificationType.choices,
    )
    title = models.CharField('Tytuł', max_length=200)
    message = models.TextField('Treść')
    data = models.JSONField('Dane dodatkowe', default=dict, blank=True)
    is_read = models.BooleanField('Przeczytane', default=False)
    read_at = models.DateTimeField('Data przeczytania', null=True, blank=True)

    # Optional link
    action_url = models.CharField('URL akcji', max_length=500, blank=True)

    created_at = models.DateTimeField('Utworzono', auto_now_add=True)

    class Meta:
        db_table = 'notifications'
        verbose_name = 'Powiadomienie'
        verbose_name_plural = 'Powiadomienia'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['is_read']),
            models.Index(fields=['created_at']),
            models.Index(fields=['type']),
        ]

    def __str__(self):
        return f'{self.user}: {self.title}'
