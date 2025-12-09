from django.contrib.auth.models import AbstractUser
from django.db import models

from .managers import UserManager


class NotificationChannel(models.TextChoices):
    """Available notification channels."""

    EMAIL = 'email', 'Email'
    SMS = 'sms', 'SMS'
    PUSH = 'push', 'Powiadomienia push'
    IN_APP = 'in_app', 'W aplikacji'


class UserRole(models.TextChoices):
    """User role choices."""

    ADMIN = 'admin', 'Administrator'
    TUTOR = 'tutor', 'Korepetytor'
    STUDENT = 'student', 'Uczeń'
    PARENT = 'parent', 'Rodzic'


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

    @property
    def is_parent(self):
        """Check if user is parent."""
        return self.role == UserRole.PARENT


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


class NotificationPreference(models.Model):
    """User notification preferences for different channels and types."""

    user = models.OneToOneField(
        'User',
        on_delete=models.CASCADE,
        related_name='notification_preferences',
        verbose_name='Użytkownik',
    )

    # Email notifications
    email_lesson_reminders = models.BooleanField(
        'Przypomnienia o lekcjach (email)',
        default=True,
    )
    email_lesson_changes = models.BooleanField(
        'Zmiany w lekcjach (email)',
        default=True,
    )
    email_messages = models.BooleanField(
        'Wiadomości (email)',
        default=True,
    )
    email_invoices = models.BooleanField(
        'Faktury (email)',
        default=True,
    )
    email_system = models.BooleanField(
        'Powiadomienia systemowe (email)',
        default=True,
    )
    email_marketing = models.BooleanField(
        'Informacje marketingowe (email)',
        default=False,
    )

    # SMS notifications
    sms_lesson_reminders = models.BooleanField(
        'Przypomnienia o lekcjach (SMS)',
        default=False,
    )
    sms_lesson_changes = models.BooleanField(
        'Zmiany w lekcjach (SMS)',
        default=True,
    )
    sms_urgent = models.BooleanField(
        'Pilne powiadomienia (SMS)',
        default=True,
    )

    # Push notifications
    push_enabled = models.BooleanField(
        'Powiadomienia push włączone',
        default=True,
    )
    push_lesson_reminders = models.BooleanField(
        'Przypomnienia o lekcjach (push)',
        default=True,
    )
    push_messages = models.BooleanField(
        'Wiadomości (push)',
        default=True,
    )

    # In-app notifications
    in_app_enabled = models.BooleanField(
        'Powiadomienia w aplikacji',
        default=True,
    )

    # Timing preferences
    reminder_hours_before = models.PositiveSmallIntegerField(
        'Godziny przed lekcją (przypomnienie)',
        default=24,
        help_text='Ile godzin przed lekcją wysłać przypomnienie',
    )
    quiet_hours_start = models.TimeField(
        'Cisza nocna od',
        null=True,
        blank=True,
        help_text='Nie wysyłaj powiadomień po tej godzinie',
    )
    quiet_hours_end = models.TimeField(
        'Cisza nocna do',
        null=True,
        blank=True,
        help_text='Nie wysyłaj powiadomień przed tą godziną',
    )

    created_at = models.DateTimeField('Utworzono', auto_now_add=True)
    updated_at = models.DateTimeField('Zaktualizowano', auto_now=True)

    class Meta:
        db_table = 'notification_preferences'
        verbose_name = 'Preferencje powiadomień'
        verbose_name_plural = 'Preferencje powiadomień'

    def __str__(self):
        return f'Preferencje: {self.user.get_full_name()}'

    @classmethod
    def get_or_create_for_user(cls, user: 'User') -> 'NotificationPreference':
        """Get or create notification preferences for user."""
        prefs, _ = cls.objects.get_or_create(user=user)
        return prefs

    def should_send(self, notification_type: str, channel: str) -> bool:
        """Check if notification should be sent based on preferences.

        Args:
            notification_type: Type of notification (lesson_reminder, message, etc.)
            channel: Channel to send through (email, sms, push, in_app)

        Returns:
            True if notification should be sent.
        """
        field_name = f'{channel}_{notification_type}'

        # Check channel-level toggle first
        if channel == 'push' and not self.push_enabled:
            return False
        if channel == 'in_app' and not self.in_app_enabled:
            return False

        # Check specific preference
        return getattr(self, field_name, True)


class UserActivity(models.Model):
    """Track user activity for analytics and security."""

    class ActivityType(models.TextChoices):
        LOGIN = 'login', 'Logowanie'
        LOGOUT = 'logout', 'Wylogowanie'
        PASSWORD_CHANGE = 'password_change', 'Zmiana hasła'
        PROFILE_UPDATE = 'profile_update', 'Aktualizacja profilu'
        LESSON_VIEW = 'lesson_view', 'Przeglądanie lekcji'
        MESSAGE_SEND = 'message_send', 'Wysłanie wiadomości'
        FILE_DOWNLOAD = 'file_download', 'Pobranie pliku'
        SETTINGS_CHANGE = 'settings_change', 'Zmiana ustawień'

    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='activities',
        verbose_name='Użytkownik',
    )
    activity_type = models.CharField(
        'Typ aktywności',
        max_length=30,
        choices=ActivityType.choices,
    )
    description = models.CharField(
        'Opis',
        max_length=255,
        blank=True,
    )
    metadata = models.JSONField(
        'Metadane',
        default=dict,
        blank=True,
    )
    ip_address = models.GenericIPAddressField(
        'Adres IP',
        null=True,
        blank=True,
    )
    user_agent = models.TextField(
        'User Agent',
        blank=True,
    )
    created_at = models.DateTimeField(
        'Utworzono',
        auto_now_add=True,
    )

    class Meta:
        db_table = 'user_activities'
        verbose_name = 'Aktywność użytkownika'
        verbose_name_plural = 'Aktywności użytkowników'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['activity_type']),
            models.Index(fields=['created_at']),
            models.Index(fields=['user', 'activity_type']),
        ]

    def __str__(self):
        return f'{self.user}: {self.get_activity_type_display()} ({self.created_at})'

    @classmethod
    def log(
        cls,
        user: 'User',
        activity_type: str,
        description: str = '',
        metadata: dict = None,
        request=None,
    ) -> 'UserActivity':
        """Log user activity.

        Args:
            user: The user performing the activity.
            activity_type: Type of activity from ActivityType choices.
            description: Optional description.
            metadata: Optional additional data.
            request: Optional HTTP request for IP/user agent.

        Returns:
            Created UserActivity instance.
        """
        ip_address = None
        user_agent = ''

        if request:
            ip_address = request.META.get('REMOTE_ADDR')
            user_agent = request.META.get('HTTP_USER_AGENT', '')

        return cls.objects.create(
            user=user,
            activity_type=activity_type,
            description=description,
            metadata=metadata or {},
            ip_address=ip_address,
            user_agent=user_agent,
        )


class UserRelationship(models.Model):
    """Track relationships between users (tutor-student, parent-student)."""

    class RelationshipType(models.TextChoices):
        TUTOR_STUDENT = 'tutor_student', 'Korepetytor-Uczeń'
        PARENT_STUDENT = 'parent_student', 'Rodzic-Uczeń'

    from_user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='relationships_from',
        verbose_name='Od użytkownika',
    )
    to_user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='relationships_to',
        verbose_name='Do użytkownika',
    )
    relationship_type = models.CharField(
        'Typ relacji',
        max_length=30,
        choices=RelationshipType.choices,
    )
    is_active = models.BooleanField(
        'Aktywna',
        default=True,
    )
    notes = models.TextField(
        'Notatki',
        blank=True,
    )
    started_at = models.DateField(
        'Data rozpoczęcia',
        null=True,
        blank=True,
    )
    ended_at = models.DateField(
        'Data zakończenia',
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(
        'Utworzono',
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        'Zaktualizowano',
        auto_now=True,
    )

    class Meta:
        db_table = 'user_relationships'
        verbose_name = 'Relacja użytkowników'
        verbose_name_plural = 'Relacje użytkowników'
        unique_together = ['from_user', 'to_user', 'relationship_type']
        indexes = [
            models.Index(fields=['from_user']),
            models.Index(fields=['to_user']),
            models.Index(fields=['relationship_type']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f'{self.from_user} -> {self.to_user} ({self.get_relationship_type_display()})'

    @classmethod
    def get_students_for_tutor(cls, tutor: 'User'):
        """Get all students for a tutor."""
        return cls.objects.filter(
            from_user=tutor,
            relationship_type=cls.RelationshipType.TUTOR_STUDENT,
            is_active=True,
        ).select_related('to_user')

    @classmethod
    def get_tutors_for_student(cls, student: 'User'):
        """Get all tutors for a student."""
        return cls.objects.filter(
            to_user=student,
            relationship_type=cls.RelationshipType.TUTOR_STUDENT,
            is_active=True,
        ).select_related('from_user')

    @classmethod
    def get_children_for_parent(cls, parent: 'User'):
        """Get all children for a parent."""
        return cls.objects.filter(
            from_user=parent,
            relationship_type=cls.RelationshipType.PARENT_STUDENT,
            is_active=True,
        ).select_related('to_user')


class UserArchive(models.Model):
    """Archive for deleted/deactivated user data (GDPR compliance)."""

    class ArchiveReason(models.TextChoices):
        USER_REQUEST = 'user_request', 'Na żądanie użytkownika'
        ADMIN_ACTION = 'admin_action', 'Akcja administratora'
        INACTIVITY = 'inactivity', 'Nieaktywność'
        GDPR_REQUEST = 'gdpr_request', 'Żądanie RODO'

    original_user_id = models.IntegerField(
        'Oryginalne ID użytkownika',
    )
    email_hash = models.CharField(
        'Hash email',
        max_length=64,
        help_text='SHA-256 hash of original email for reference',
    )
    archived_data = models.JSONField(
        'Zarchiwizowane dane',
        help_text='Encrypted user data',
    )
    reason = models.CharField(
        'Powód archiwizacji',
        max_length=30,
        choices=ArchiveReason.choices,
    )
    archived_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='archived_users',
        verbose_name='Zarchiwizowane przez',
    )
    notes = models.TextField(
        'Notatki',
        blank=True,
    )
    retention_until = models.DateField(
        'Przechowywać do',
        help_text='Date until which archive must be retained',
    )
    is_anonymized = models.BooleanField(
        'Zanonimizowane',
        default=False,
    )
    anonymized_at = models.DateTimeField(
        'Data anonimizacji',
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(
        'Utworzono',
        auto_now_add=True,
    )

    class Meta:
        db_table = 'user_archives'
        verbose_name = 'Archiwum użytkownika'
        verbose_name_plural = 'Archiwa użytkowników'
        indexes = [
            models.Index(fields=['original_user_id']),
            models.Index(fields=['email_hash']),
            models.Index(fields=['retention_until']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f'Archiwum #{self.original_user_id} ({self.get_reason_display()})'


class UserVerification(models.Model):
    """User verification workflow for email/phone verification."""

    class VerificationType(models.TextChoices):
        EMAIL = 'email', 'Email'
        PHONE = 'phone', 'Telefon'
        IDENTITY = 'identity', 'Tożsamość'

    class VerificationStatus(models.TextChoices):
        PENDING = 'pending', 'Oczekujące'
        VERIFIED = 'verified', 'Zweryfikowane'
        FAILED = 'failed', 'Niepowodzenie'
        EXPIRED = 'expired', 'Wygasłe'

    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='verifications',
        verbose_name='Użytkownik',
    )
    verification_type = models.CharField(
        'Typ weryfikacji',
        max_length=20,
        choices=VerificationType.choices,
    )
    status = models.CharField(
        'Status',
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
    )
    token = models.CharField(
        'Token',
        max_length=64,
        unique=True,
    )
    value_to_verify = models.CharField(
        'Wartość do weryfikacji',
        max_length=255,
        help_text='Email or phone number being verified',
    )
    attempts = models.PositiveSmallIntegerField(
        'Liczba prób',
        default=0,
    )
    max_attempts = models.PositiveSmallIntegerField(
        'Maksymalna liczba prób',
        default=3,
    )
    expires_at = models.DateTimeField(
        'Wygasa',
    )
    verified_at = models.DateTimeField(
        'Zweryfikowano',
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(
        'Utworzono',
        auto_now_add=True,
    )

    class Meta:
        db_table = 'user_verifications'
        verbose_name = 'Weryfikacja użytkownika'
        verbose_name_plural = 'Weryfikacje użytkowników'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['token']),
            models.Index(fields=['status']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f'{self.user}: {self.get_verification_type_display()} ({self.get_status_display()})'

    @property
    def is_expired(self) -> bool:
        """Check if verification has expired."""
        from django.utils import timezone
        return timezone.now() > self.expires_at

    @property
    def can_retry(self) -> bool:
        """Check if user can retry verification."""
        return self.attempts < self.max_attempts and not self.is_expired

    def verify(self, token: str) -> bool:
        """Attempt to verify with given token.

        Args:
            token: The verification token to check.

        Returns:
            True if verification successful.
        """
        from django.utils import timezone

        self.attempts += 1
        self.save(update_fields=['attempts'])

        if self.is_expired:
            self.status = self.VerificationStatus.EXPIRED
            self.save(update_fields=['status'])
            return False

        if self.attempts > self.max_attempts:
            self.status = self.VerificationStatus.FAILED
            self.save(update_fields=['status'])
            return False

        if token == self.token:
            self.status = self.VerificationStatus.VERIFIED
            self.verified_at = timezone.now()
            self.save(update_fields=['status', 'verified_at'])
            return True

        return False

    @classmethod
    def create_for_user(
        cls,
        user: 'User',
        verification_type: str,
        value: str,
        expires_hours: int = 24,
    ) -> 'UserVerification':
        """Create a new verification request.

        Args:
            user: User to verify.
            verification_type: Type of verification.
            value: Email or phone to verify.
            expires_hours: Hours until expiration.

        Returns:
            Created UserVerification instance.
        """
        import secrets
        from django.utils import timezone
        from datetime import timedelta

        # Invalidate previous pending verifications of same type
        cls.objects.filter(
            user=user,
            verification_type=verification_type,
            status=cls.VerificationStatus.PENDING,
        ).update(status=cls.VerificationStatus.EXPIRED)

        return cls.objects.create(
            user=user,
            verification_type=verification_type,
            value_to_verify=value,
            token=secrets.token_urlsafe(32),
            expires_at=timezone.now() + timedelta(hours=expires_hours),
        )


class ParentAccess(models.Model):
    """Parent portal access configuration."""

    class AccessLevel(models.TextChoices):
        VIEW_ONLY = 'view_only', 'Tylko podgląd'
        LIMITED = 'limited', 'Ograniczony'
        FULL = 'full', 'Pełny'

    parent = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='parent_access_grants',
        verbose_name='Rodzic',
        null=True,
        blank=True,
    )
    student = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='parent_access_received',
        verbose_name='Uczeń',
    )
    access_level = models.CharField(
        'Poziom dostępu',
        max_length=20,
        choices=AccessLevel.choices,
        default=AccessLevel.VIEW_ONLY,
    )
    is_active = models.BooleanField(
        'Aktywny',
        default=True,
    )

    # Permission flags
    can_view_lessons = models.BooleanField(
        'Może przeglądać lekcje',
        default=True,
    )
    can_view_attendance = models.BooleanField(
        'Może przeglądać obecności',
        default=True,
    )
    can_view_grades = models.BooleanField(
        'Może przeglądać oceny',
        default=True,
    )
    can_view_invoices = models.BooleanField(
        'Może przeglądać faktury',
        default=True,
    )
    can_message_tutors = models.BooleanField(
        'Może pisać do korepetytorów',
        default=True,
    )
    can_cancel_lessons = models.BooleanField(
        'Może odwoływać lekcje',
        default=False,
    )
    can_reschedule_lessons = models.BooleanField(
        'Może przełożyć lekcje',
        default=False,
    )

    # Invitation tracking
    invited_email = models.EmailField(
        'Zaproszony email',
        blank=True,
    )
    invitation_token = models.CharField(
        'Token zaproszenia',
        max_length=64,
        blank=True,
    )
    invitation_sent_at = models.DateTimeField(
        'Zaproszenie wysłane',
        null=True,
        blank=True,
    )
    invitation_accepted_at = models.DateTimeField(
        'Zaproszenie zaakceptowane',
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField('Utworzono', auto_now_add=True)
    updated_at = models.DateTimeField('Zaktualizowano', auto_now=True)

    class Meta:
        db_table = 'parent_access'
        verbose_name = 'Dostęp rodzica'
        verbose_name_plural = 'Dostępy rodziców'
        unique_together = ['parent', 'student']
        indexes = [
            models.Index(fields=['parent']),
            models.Index(fields=['student']),
            models.Index(fields=['is_active']),
            models.Index(fields=['invitation_token']),
        ]

    def __str__(self):
        return f'{self.parent} -> {self.student} ({self.get_access_level_display()})'

    @classmethod
    def create_invitation(
        cls,
        student: 'User',
        parent_email: str,
        access_level: str = 'view_only',
        created_by: 'User' = None,
    ) -> 'ParentAccess':
        """Create parent invitation.

        Args:
            student: Student user.
            parent_email: Email to invite.
            access_level: Level of access to grant.
            created_by: User creating the invitation.

        Returns:
            Created ParentAccess with invitation token.
        """
        import secrets
        from django.utils import timezone

        # Check if parent already exists
        from django.contrib.auth import get_user_model
        User = get_user_model()

        parent = User.objects.filter(email=parent_email).first()

        access = cls.objects.create(
            parent=parent,
            student=student,
            access_level=access_level,
            is_active=False,  # Not active until invitation accepted
            invited_email=parent_email,
            invitation_token=secrets.token_urlsafe(32),
            invitation_sent_at=timezone.now() if parent is None else None,
        )

        # If parent already exists and has account, activate immediately
        if parent:
            access.is_active = True
            access.invitation_accepted_at = timezone.now()
            access.save(update_fields=['is_active', 'invitation_accepted_at'])

        return access

    def accept_invitation(self, parent: 'User') -> bool:
        """Accept invitation by parent user.

        Args:
            parent: Parent user accepting invitation.

        Returns:
            True if accepted successfully.
        """
        from django.utils import timezone

        if self.invitation_accepted_at:
            return False

        self.parent = parent
        self.is_active = True
        self.invitation_accepted_at = timezone.now()
        self.save(update_fields=['parent', 'is_active', 'invitation_accepted_at'])
        return True
