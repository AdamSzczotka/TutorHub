from django.contrib.auth.models import AbstractUser
from django.db import models

from .managers import UserManager


class UserRole(models.TextChoices):
    """User role choices."""

    ADMIN = 'admin', 'Administrator'
    TUTOR = 'tutor', 'Korepetytor'
    STUDENT = 'student', 'Uczeń'


class User(AbstractUser):
    """Custom User model with email as username."""

    username = None  # Remove username field
    email = models.EmailField('Email', unique=True)

    # Profile fields
    role = models.CharField(
        'Rola',
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.STUDENT,
    )
    phone = models.CharField('Telefon', max_length=20, blank=True)
    avatar = models.ImageField(
        'Avatar',
        upload_to='avatars/',
        blank=True,
        null=True,
    )

    # Status flags
    is_profile_completed = models.BooleanField(
        'Profil uzupełniony',
        default=False,
    )
    first_login = models.BooleanField(
        'Pierwsze logowanie',
        default=True,
    )

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        db_table = 'users'
        verbose_name = 'Użytkownik'
        verbose_name_plural = 'Użytkownicy'
        ordering = ['-date_joined']

    def __str__(self):
        return f'{self.get_full_name()} ({self.email})'

    @property
    def is_admin(self):
        """Check if user is admin."""
        return self.role == UserRole.ADMIN

    @property
    def is_tutor(self):
        """Check if user is tutor."""
        return self.role == UserRole.TUTOR

    @property
    def is_student(self):
        """Check if user is student."""
        return self.role == UserRole.STUDENT


class UserCreationLog(models.Model):
    """Audit log for admin-created users."""

    created_user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='creation_logs',
    )
    created_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        related_name='users_created',
        null=True,
    )
    temp_password_hash = models.CharField(
        'Hash hasła tymczasowego',
        max_length=255,
        blank=True,
        help_text='For audit purposes only',
    )
    email_sent = models.BooleanField('Email wysłany', default=False)
    email_sent_at = models.DateTimeField('Data wysłania', null=True, blank=True)
    first_login_at = models.DateTimeField('Pierwsze logowanie', null=True, blank=True)
    profile_completed_at = models.DateTimeField(
        'Profil uzupełniony',
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField('Utworzono', auto_now_add=True)

    class Meta:
        db_table = 'user_creation_logs'
        verbose_name = 'Log utworzenia użytkownika'
        verbose_name_plural = 'Logi utworzenia użytkowników'
        indexes = [
            models.Index(fields=['created_user']),
            models.Index(fields=['created_by']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f'Log: {self.created_user} (utworzony przez {self.created_by})'
