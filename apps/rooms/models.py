from django.db import models


class Room(models.Model):
    """Room/venue for lessons."""

    name = models.CharField('Nazwa', max_length=100, unique=True)
    capacity = models.PositiveIntegerField('Pojemność')
    location = models.CharField('Lokalizacja', max_length=200, blank=True)
    description = models.TextField('Opis', blank=True)
    equipment = models.JSONField(
        'Wyposażenie',
        default=dict,
        blank=True,
        help_text='Equipment as JSON object',
    )
    is_active = models.BooleanField('Aktywna', default=True)
    is_virtual = models.BooleanField('Wirtualna', default=False)

    created_at = models.DateTimeField('Utworzono', auto_now_add=True)
    updated_at = models.DateTimeField('Zaktualizowano', auto_now=True)

    class Meta:
        db_table = 'rooms'
        verbose_name = 'Sala'
        verbose_name_plural = 'Sale'
        ordering = ['name']

    def __str__(self):
        return self.name
