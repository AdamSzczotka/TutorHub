from django.db import models


class Subject(models.Model):
    """Academic subject."""

    name = models.CharField('Nazwa', max_length=100, unique=True)
    description = models.TextField('Opis', blank=True)
    icon = models.CharField('Ikona', max_length=50, blank=True)
    color = models.CharField('Kolor', max_length=7, blank=True)
    is_active = models.BooleanField('Aktywny', default=True)

    created_at = models.DateTimeField('Utworzono', auto_now_add=True)
    updated_at = models.DateTimeField('Zaktualizowano', auto_now=True)

    class Meta:
        db_table = 'subjects'
        verbose_name = 'Przedmiot'
        verbose_name_plural = 'Przedmioty'
        ordering = ['name']

    def __str__(self):
        return self.name


class Level(models.Model):
    """Education level/class grouping."""

    name = models.CharField('Nazwa', max_length=100, unique=True)
    description = models.TextField('Opis', blank=True)
    order_index = models.PositiveIntegerField('Kolejność', default=0)
    color = models.CharField('Kolor', max_length=7, blank=True)

    created_at = models.DateTimeField('Utworzono', auto_now_add=True)
    updated_at = models.DateTimeField('Zaktualizowano', auto_now=True)

    class Meta:
        db_table = 'levels'
        verbose_name = 'Poziom'
        verbose_name_plural = 'Poziomy'
        ordering = ['order_index']
        indexes = [
            models.Index(fields=['order_index']),
        ]

    def __str__(self):
        return self.name


class SubjectLevel(models.Model):
    """Many-to-many relationship between subjects and levels."""

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='subject_levels',
    )
    level = models.ForeignKey(
        Level,
        on_delete=models.CASCADE,
        related_name='subject_levels',
    )

    class Meta:
        db_table = 'subject_levels'
        verbose_name = 'Przedmiot-Poziom'
        verbose_name_plural = 'Przedmioty-Poziomy'
        unique_together = ['subject', 'level']

    def __str__(self):
        return f'{self.subject.name} - {self.level.name}'
