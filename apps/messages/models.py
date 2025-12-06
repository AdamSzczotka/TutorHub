from django.conf import settings
from django.db import models


class Message(models.Model):
    """Internal messaging system."""

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        verbose_name='Nadawca',
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_messages',
        verbose_name='Odbiorca',
    )

    subject = models.CharField('Temat', max_length=200, blank=True)
    content = models.TextField('Treść')
    is_read = models.BooleanField('Przeczytana', default=False)
    read_at = models.DateTimeField('Data przeczytania', null=True, blank=True)
    attachments = models.JSONField('Załączniki', default=list, blank=True)

    # Thread support
    parent_message = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        related_name='replies',
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField('Utworzono', auto_now_add=True)

    class Meta:
        db_table = 'messages'
        verbose_name = 'Wiadomość'
        verbose_name_plural = 'Wiadomości'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sender']),
            models.Index(fields=['recipient']),
            models.Index(fields=['is_read']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f'{self.sender} -> {self.recipient}: {self.subject or "Brak tematu"}'
