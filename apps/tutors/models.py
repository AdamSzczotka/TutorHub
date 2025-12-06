from django.conf import settings
from django.db import models


class TutorProfile(models.Model):
    """Extended profile for tutors."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tutor_profile',
        verbose_name='Użytkownik',
    )
    bio = models.TextField('Opis', blank=True)
    hourly_rate = models.DecimalField(
        'Stawka godzinowa',
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
    )
    experience_years = models.PositiveIntegerField(
        'Lata doświadczenia',
        null=True,
        blank=True,
    )
    education = models.TextField('Wykształcenie', blank=True)
    certifications = models.JSONField(
        'Certyfikaty',
        default=list,
        blank=True,
    )
    availability_hours = models.JSONField(
        'Godziny dostępności',
        default=dict,
        blank=True,
        help_text='Weekly availability schedule as JSON',
    )
    is_verified = models.BooleanField('Zweryfikowany', default=False)
    verification_date = models.DateTimeField(
        'Data weryfikacji',
        null=True,
        blank=True,
    )
    rating_avg = models.DecimalField(
        'Średnia ocena',
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
    )
    lessons_completed = models.PositiveIntegerField(
        'Ukończone lekcje',
        default=0,
    )

    created_at = models.DateTimeField('Utworzono', auto_now_add=True)
    updated_at = models.DateTimeField('Zaktualizowano', auto_now=True)

    class Meta:
        db_table = 'tutor_profiles'
        verbose_name = 'Profil korepetytora'
        verbose_name_plural = 'Profile korepetytorów'

    def __str__(self):
        return f'Profil: {self.user.get_full_name()}'


class TutorSubject(models.Model):
    """Junction table for tutor-subject-level assignments."""

    tutor = models.ForeignKey(
        TutorProfile,
        on_delete=models.CASCADE,
        related_name='tutor_subjects',
    )
    subject = models.ForeignKey(
        'subjects.Subject',
        on_delete=models.CASCADE,
        related_name='tutor_assignments',
    )
    level = models.ForeignKey(
        'subjects.Level',
        on_delete=models.CASCADE,
        related_name='tutor_assignments',
    )

    rate_per_hour = models.DecimalField(
        'Stawka za godzinę',
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
    )
    is_active = models.BooleanField('Aktywny', default=True)

    created_at = models.DateTimeField('Utworzono', auto_now_add=True)
    updated_at = models.DateTimeField('Zaktualizowano', auto_now=True)

    class Meta:
        db_table = 'tutor_subjects'
        verbose_name = 'Przedmiot korepetytora'
        verbose_name_plural = 'Przedmioty korepetytorów'
        unique_together = ['tutor', 'subject', 'level']

    def __str__(self):
        return f'{self.tutor.user.get_full_name()} - {self.subject.name} ({self.level.name})'
