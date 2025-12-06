from django.conf import settings
from django.db import models


class StudentProfile(models.Model):
    """Extended profile for students."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='student_profile',
        verbose_name='Użytkownik',
    )
    class_name = models.CharField(
        'Klasa',
        max_length=10,
        blank=True,
        help_text='np. 7A, 3LO',
    )
    current_level = models.CharField(
        'Aktualny poziom',
        max_length=50,
        blank=True,
    )
    learning_goals = models.TextField('Cele nauki', blank=True)
    parent_name = models.CharField('Imię rodzica', max_length=100, blank=True)
    parent_phone = models.CharField('Telefon rodzica', max_length=20, blank=True)
    parent_email = models.EmailField('Email rodzica', blank=True)
    secondary_parent_name = models.CharField(
        'Imię drugiego rodzica',
        max_length=100,
        blank=True,
    )
    secondary_parent_phone = models.CharField(
        'Telefon drugiego rodzica',
        max_length=20,
        blank=True,
    )
    emergency_contact = models.CharField(
        'Kontakt awaryjny',
        max_length=100,
        blank=True,
    )
    notes = models.TextField('Notatki', blank=True)
    joined_at = models.DateTimeField('Data dołączenia', auto_now_add=True)
    total_lessons = models.PositiveIntegerField('Wszystkie lekcje', default=0)
    completed_lessons = models.PositiveIntegerField('Ukończone lekcje', default=0)

    created_at = models.DateTimeField('Utworzono', auto_now_add=True)
    updated_at = models.DateTimeField('Zaktualizowano', auto_now=True)

    class Meta:
        db_table = 'student_profiles'
        verbose_name = 'Profil ucznia'
        verbose_name_plural = 'Profile uczniów'

    def __str__(self):
        return f'Profil: {self.user.get_full_name()}'

    @property
    def attendance_rate(self):
        """Calculate attendance rate as percentage."""
        if self.total_lessons == 0:
            return 0
        return (self.completed_lessons / self.total_lessons) * 100
