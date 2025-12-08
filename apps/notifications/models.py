import uuid

from django.conf import settings
from django.db import models


class NotificationType(models.TextChoices):
    SYSTEM = 'SYSTEM', 'Systemowe'
    MESSAGE = 'MESSAGE', 'Wiadomość'
    EVENT = 'EVENT', 'Wydarzenie'
    ATTENDANCE = 'ATTENDANCE', 'Obecność'
    CANCELLATION = 'CANCELLATION', 'Anulowanie'
    INVOICE = 'INVOICE', 'Faktura'
    ANNOUNCEMENT = 'ANNOUNCEMENT', 'Ogłoszenie'
    REMINDER = 'REMINDER', 'Przypomnienie'


class NotificationPriority(models.TextChoices):
    LOW = 'LOW', 'Niski'
    NORMAL = 'NORMAL', 'Normalny'
    HIGH = 'HIGH', 'Wysoki'
    URGENT = 'URGENT', 'Pilny'


class Notification(models.Model):
    """Model powiadomienia."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
    )

    # Content
    title = models.CharField('Tytuł', max_length=200)
    message = models.TextField('Treść')
    type = models.CharField(
        'Typ',
        max_length=20,
        choices=NotificationType.choices,
        default=NotificationType.SYSTEM,
    )
    priority = models.CharField(
        'Priorytet',
        max_length=20,
        choices=NotificationPriority.choices,
        default=NotificationPriority.NORMAL,
    )

    # Action/Link
    action_url = models.CharField('URL akcji', max_length=500, blank=True)
    action_label = models.CharField('Etykieta akcji', max_length=50, blank=True)

    # Related entities
    related_entity_type = models.CharField(
        'Typ powiązanego obiektu',
        max_length=50,
        blank=True,
    )
    related_entity_id = models.CharField(
        'ID powiązanego obiektu',
        max_length=50,
        blank=True,
    )

    # Status
    is_read = models.BooleanField('Przeczytane', default=False)
    read_at = models.DateTimeField('Przeczytano', null=True, blank=True)
    is_archived = models.BooleanField('Zarchiwizowane', default=False)
    archived_at = models.DateTimeField('Zarchiwizowano', null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField('Wygasa', null=True, blank=True)

    class Meta:
        db_table = 'notifications'
        verbose_name = 'Powiadomienie'
        verbose_name_plural = 'Powiadomienia'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', '-created_at']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['type', 'priority']),
        ]

    def __str__(self):
        return f'{self.title} - {self.user}'


# NotificationPreference is defined in apps.accounts.models
# Use: from apps.accounts.models import NotificationPreference


class AnnouncementType(models.TextChoices):
    INFO = 'INFO', 'Informacja'
    WARNING = 'WARNING', 'Ostrzeżenie'
    SUCCESS = 'SUCCESS', 'Sukces'
    ERROR = 'ERROR', 'Błąd'


class Announcement(models.Model):
    """Model ogłoszenia systemowego."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Content
    title = models.CharField('Tytuł', max_length=200)
    content = models.TextField('Treść')
    type = models.CharField(
        'Typ',
        max_length=20,
        choices=AnnouncementType.choices,
        default=AnnouncementType.INFO,
    )

    # Targeting
    target_roles = models.JSONField(
        'Role docelowe',
        default=list,
        help_text='Lista ról, dla których jest widoczne',
    )
    is_pinned = models.BooleanField('Przypięte', default=False)

    # Scheduling
    publish_at = models.DateTimeField('Data publikacji', auto_now_add=True)
    expires_at = models.DateTimeField('Data wygaśnięcia', null=True, blank=True)

    # Metadata
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_announcements',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'announcements'
        verbose_name = 'Ogłoszenie'
        verbose_name_plural = 'Ogłoszenia'
        ordering = ['-is_pinned', '-publish_at']
        indexes = [
            models.Index(fields=['publish_at', 'expires_at']),
            models.Index(fields=['is_pinned']),
        ]

    def __str__(self):
        return self.title
