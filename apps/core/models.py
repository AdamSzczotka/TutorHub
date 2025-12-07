from django.conf import settings
from django.db import models


class TimeStampedModel(models.Model):
    """Abstract base model with timestamps."""

    created_at = models.DateTimeField('Utworzono', auto_now_add=True)
    updated_at = models.DateTimeField('Zaktualizowano', auto_now=True)

    class Meta:
        abstract = True


class AuditLog(models.Model):
    """System-wide audit trail."""

    ACTION_CHOICES = [
        ('create', 'Utworzenie'),
        ('update', 'Aktualizacja'),
        ('delete', 'Usunięcie'),
        ('export', 'Eksport'),
        ('bulk_update', 'Aktualizacja zbiorcza'),
        ('login', 'Logowanie'),
        ('logout', 'Wylogowanie'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='audit_logs',
        null=True,
        blank=True,
    )
    action = models.CharField('Akcja', max_length=20, choices=ACTION_CHOICES)
    model_type = models.CharField('Typ modelu', max_length=100)
    model_id = models.CharField('ID rekordu', max_length=100, blank=True)
    old_values = models.JSONField('Poprzednie wartości', null=True, blank=True)
    new_values = models.JSONField('Nowe wartości', null=True, blank=True)
    ip_address = models.GenericIPAddressField('Adres IP', null=True, blank=True)
    user_agent = models.TextField('User Agent', blank=True)

    created_at = models.DateTimeField('Utworzono', auto_now_add=True)

    class Meta:
        db_table = 'audit_logs'
        verbose_name = 'Log audytu'
        verbose_name_plural = 'Logi audytu'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['model_type']),
            models.Index(fields=['created_at']),
            models.Index(fields=['action']),
        ]

    def __str__(self):
        return f'{self.action} - {self.model_type} - {self.created_at}'


class SystemSetting(models.Model):
    """Key-value storage for system settings."""

    key = models.CharField('Klucz', max_length=100, unique=True)
    value = models.JSONField('Wartosc', default=dict)
    description = models.TextField('Opis', blank=True)

    created_at = models.DateTimeField('Utworzono', auto_now_add=True)
    updated_at = models.DateTimeField('Zaktualizowano', auto_now=True)

    class Meta:
        db_table = 'system_settings'
        verbose_name = 'Ustawienie systemowe'
        verbose_name_plural = 'Ustawienia systemowe'

    def __str__(self):
        return self.key

    @classmethod
    def get(cls, key: str, default=None):
        """Get a setting value by key."""
        try:
            setting = cls.objects.get(key=key)
            return setting.value
        except cls.DoesNotExist:
            return default

    @classmethod
    def set(cls, key: str, value, description: str = ''):
        """Set a setting value by key."""
        setting, _ = cls.objects.update_or_create(
            key=key,
            defaults={'value': value, 'description': description}
        )
        return setting
