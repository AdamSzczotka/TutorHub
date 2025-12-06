# Phase 1 - Sprint 1.1: Database Models & Schema (Django)

## Tasks 013-020: Complete Database Foundation

> **Duration**: Week 1 of Phase 1 (5 working days)
> **Goal**: Implement complete database schema with Django Models, relations, and indexes
> **Critical**: Foundation for all application features

---

## SPRINT OVERVIEW

| Task ID | Description                         | Priority | Dependencies     |
| ------- | ----------------------------------- | -------- | ---------------- |
| 013     | Django Models - main models         | Critical | Phase 0 complete |
| 014     | Django Models - relationship models | Critical | Task 013         |
| 015     | Django Models - system models       | Critical | Task 013         |
| 016     | Model choices and enums             | Critical | Task 013         |
| 017     | Model relationships & managers      | Critical | Tasks 013-016    |
| 018     | Database indexes implementation     | High     | Task 017         |
| 019     | Initial migrations                  | Critical | Tasks 013-018    |
| 020     | Seed data (management command)      | High     | Task 019         |

---

## DETAILED TASK BREAKDOWN

### Task 013: Django Models - Main Models

**Reference**: ProjectSpecification.md section 3.1

#### Tutor Profile Model

**File**: `apps/tutors/models.py`

```python
from django.db import models
from django.conf import settings


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
```

#### Student Profile Model

**File**: `apps/students/models.py`

```python
from django.db import models
from django.conf import settings


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
```

#### Lesson (Event) Model

**File**: `apps/lessons/models.py`

```python
from django.db import models
from django.conf import settings


class LessonStatus(models.TextChoices):
    SCHEDULED = 'scheduled', 'Zaplanowana'
    ONGOING = 'ongoing', 'W trakcie'
    COMPLETED = 'completed', 'Ukończona'
    CANCELLED = 'cancelled', 'Anulowana'


class Lesson(models.Model):
    """Lesson/Event model - core of the scheduling system."""

    title = models.CharField('Tytuł', max_length=200)
    description = models.TextField('Opis', blank=True)

    subject = models.ForeignKey(
        'subjects.Subject',
        on_delete=models.PROTECT,
        related_name='lessons',
        verbose_name='Przedmiot',
    )
    level = models.ForeignKey(
        'subjects.Level',
        on_delete=models.PROTECT,
        related_name='lessons',
        verbose_name='Poziom',
    )
    tutor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='tutor_lessons',
        verbose_name='Korepetytor',
        limit_choices_to={'role': 'tutor'},
    )
    room = models.ForeignKey(
        'rooms.Room',
        on_delete=models.SET_NULL,
        related_name='lessons',
        verbose_name='Sala',
        null=True,
        blank=True,
    )

    start_time = models.DateTimeField('Czas rozpoczęcia')
    end_time = models.DateTimeField('Czas zakończenia')

    is_group_lesson = models.BooleanField('Lekcja grupowa', default=False)
    max_participants = models.PositiveIntegerField(
        'Maksymalna liczba uczestników',
        null=True,
        blank=True,
    )
    status = models.CharField(
        'Status',
        max_length=20,
        choices=LessonStatus.choices,
        default=LessonStatus.SCHEDULED,
    )
    notes = models.TextField('Notatki', blank=True)
    color = models.CharField(
        'Kolor',
        max_length=7,
        blank=True,
        help_text='Hex color for calendar display',
    )

    # Recurrence
    is_recurring = models.BooleanField('Cykliczna', default=False)
    recurrence_rule = models.JSONField(
        'Reguła powtarzania',
        null=True,
        blank=True,
    )
    parent_lesson = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        related_name='occurrences',
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField('Utworzono', auto_now_add=True)
    updated_at = models.DateTimeField('Zaktualizowano', auto_now=True)

    class Meta:
        db_table = 'lessons'
        verbose_name = 'Lekcja'
        verbose_name_plural = 'Lekcje'
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['start_time']),
            models.Index(fields=['end_time']),
            models.Index(fields=['tutor']),
            models.Index(fields=['room']),
            models.Index(fields=['status']),
            models.Index(fields=['start_time', 'end_time']),
        ]

    def __str__(self):
        return f'{self.title} - {self.start_time.strftime("%Y-%m-%d %H:%M")}'

    @property
    def duration_minutes(self):
        """Get lesson duration in minutes."""
        delta = self.end_time - self.start_time
        return int(delta.total_seconds() / 60)

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.start_time >= self.end_time:
            raise ValidationError('Czas zakończenia musi być po czasie rozpoczęcia.')

        if self.is_group_lesson and not self.max_participants:
            raise ValidationError(
                'Lekcja grupowa wymaga określenia maksymalnej liczby uczestników.'
            )
```

#### Room Model

**File**: `apps/rooms/models.py`

```python
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
```

#### Subject & Level Models

**File**: `apps/subjects/models.py`

```python
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
```

---

### Task 014: Django Models - Relationship Models

#### Lesson-Student Assignment

**File**: `apps/lessons/models.py` (continued)

```python
class AttendanceStatus(models.TextChoices):
    UNKNOWN = 'unknown', 'Nieznany'
    PRESENT = 'present', 'Obecny'
    ABSENT = 'absent', 'Nieobecny'
    LATE = 'late', 'Spóźniony'
    EXCUSED = 'excused', 'Usprawiedliwiony'


class LessonStudent(models.Model):
    """Junction table for lesson-student assignments with attendance."""

    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='lesson_students',
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='student_lessons',
        limit_choices_to={'role': 'student'},
    )

    attendance_status = models.CharField(
        'Status obecności',
        max_length=20,
        choices=AttendanceStatus.choices,
        default=AttendanceStatus.UNKNOWN,
    )
    attendance_marked_at = models.DateTimeField(
        'Czas oznaczenia',
        null=True,
        blank=True,
    )
    attendance_marked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='marked_attendances',
        null=True,
        blank=True,
    )
    notes = models.TextField('Notatki', blank=True)

    created_at = models.DateTimeField('Utworzono', auto_now_add=True)
    updated_at = models.DateTimeField('Zaktualizowano', auto_now=True)

    class Meta:
        db_table = 'lesson_students'
        verbose_name = 'Uczeń na lekcji'
        verbose_name_plural = 'Uczniowie na lekcjach'
        unique_together = ['lesson', 'student']
        indexes = [
            models.Index(fields=['lesson']),
            models.Index(fields=['student']),
            models.Index(fields=['attendance_status']),
        ]

    def __str__(self):
        return f'{self.student.get_full_name()} - {self.lesson.title}'
```

#### Tutor-Subject Assignment

**File**: `apps/tutors/models.py` (continued)

```python
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
```

---

### Task 015: Django Models - System Models

#### User Creation Log

**File**: `apps/accounts/models.py` (continued)

```python
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
```

#### Audit Log

**File**: `apps/core/models.py`

```python
from django.db import models
from django.conf import settings


class AuditLog(models.Model):
    """System-wide audit trail."""

    ACTION_CHOICES = [
        ('create', 'Utworzenie'),
        ('update', 'Aktualizacja'),
        ('delete', 'Usunięcie'),
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
```

#### Message Model

**File**: `apps/messages/models.py`

```python
from django.db import models
from django.conf import settings


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
```

#### Notification Model

**File**: `apps/notifications/models.py`

```python
from django.db import models
from django.conf import settings


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
```

---

### Task 016: Model Choices and Enums

**File**: `apps/core/choices.py`

```python
from django.db import models


class UserRole(models.TextChoices):
    ADMIN = 'admin', 'Administrator'
    TUTOR = 'tutor', 'Korepetytor'
    STUDENT = 'student', 'Uczeń'


class LessonStatus(models.TextChoices):
    SCHEDULED = 'scheduled', 'Zaplanowana'
    ONGOING = 'ongoing', 'W trakcie'
    COMPLETED = 'completed', 'Ukończona'
    CANCELLED = 'cancelled', 'Anulowana'


class AttendanceStatus(models.TextChoices):
    UNKNOWN = 'unknown', 'Nieznany'
    PRESENT = 'present', 'Obecny'
    ABSENT = 'absent', 'Nieobecny'
    LATE = 'late', 'Spóźniony'
    EXCUSED = 'excused', 'Usprawiedliwiony'


class InvoiceStatus(models.TextChoices):
    DRAFT = 'draft', 'Szkic'
    GENERATED = 'generated', 'Wygenerowana'
    SENT = 'sent', 'Wysłana'
    PAID = 'paid', 'Opłacona'
    OVERDUE = 'overdue', 'Zaległa'
    CANCELLED = 'cancelled', 'Anulowana'
    CORRECTED = 'corrected', 'Skorygowana'


class CancellationStatus(models.TextChoices):
    PENDING = 'pending', 'Oczekująca'
    APPROVED = 'approved', 'Zatwierdzona'
    REJECTED = 'rejected', 'Odrzucona'


class MakeupStatus(models.TextChoices):
    PENDING = 'pending', 'Oczekująca'
    SCHEDULED = 'scheduled', 'Zaplanowana'
    COMPLETED = 'completed', 'Ukończona'
    EXPIRED = 'expired', 'Wygasła'


class LeadStatus(models.TextChoices):
    NEW = 'new', 'Nowy'
    CONTACTED = 'contacted', 'Skontaktowany'
    QUALIFIED = 'qualified', 'Kwalifikowany'
    CONVERTED = 'converted', 'Skonwertowany'
    LOST = 'lost', 'Utracony'
```

---

### Task 017: Model Relationships & Managers

**File**: `apps/lessons/managers.py`

```python
from django.db import models
from django.utils import timezone


class LessonQuerySet(models.QuerySet):
    """Custom QuerySet for Lesson model."""

    def upcoming(self):
        """Get upcoming lessons."""
        return self.filter(
            start_time__gte=timezone.now(),
            status='scheduled',
        ).order_by('start_time')

    def past(self):
        """Get past lessons."""
        return self.filter(
            end_time__lt=timezone.now(),
        ).order_by('-start_time')

    def for_tutor(self, user):
        """Get lessons for a specific tutor."""
        return self.filter(tutor=user)

    def for_student(self, user):
        """Get lessons for a specific student."""
        return self.filter(lesson_students__student=user)

    def in_date_range(self, start_date, end_date):
        """Get lessons in a date range."""
        return self.filter(
            start_time__date__gte=start_date,
            start_time__date__lte=end_date,
        )

    def with_attendance(self):
        """Prefetch attendance data."""
        return self.prefetch_related(
            'lesson_students',
            'lesson_students__student',
        )


class LessonManager(models.Manager):
    """Custom Manager for Lesson model."""

    def get_queryset(self):
        return LessonQuerySet(self.model, using=self._db)

    def upcoming(self):
        return self.get_queryset().upcoming()

    def for_tutor(self, user):
        return self.get_queryset().for_tutor(user)

    def for_student(self, user):
        return self.get_queryset().for_student(user)
```

Update the Lesson model to use the manager:

```python
# In apps/lessons/models.py
class Lesson(models.Model):
    # ... fields ...

    objects = LessonManager()

    # ... rest of model ...
```

---

### Task 018: Database Indexes Implementation

All indexes are already defined in the models above using `models.Index` in `Meta.indexes`.

**Summary of indexes**:

| Model | Indexed Fields |
|-------|----------------|
| User | email, role, is_active |
| Lesson | start_time, end_time, tutor, room, status |
| LessonStudent | lesson, student, attendance_status |
| Message | sender, recipient, is_read, created_at |
| Notification | user, is_read, created_at, type |
| AuditLog | user, model_type, created_at, action |

---

### Task 019: Initial Migrations

```bash
# Create migrations for all apps
python manage.py makemigrations accounts
python manage.py makemigrations tutors
python manage.py makemigrations students
python manage.py makemigrations subjects
python manage.py makemigrations rooms
python manage.py makemigrations lessons
python manage.py makemigrations messages
python manage.py makemigrations notifications
python manage.py makemigrations core

# Apply all migrations
python manage.py migrate

# Check migration status
python manage.py showmigrations
```

---

### Task 020: Seed Data (Management Command)

**File**: `apps/core/management/commands/seed_data.py`

```python
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.subjects.models import Subject, Level, SubjectLevel
from apps.rooms.models import Room


User = get_user_model()


class Command(BaseCommand):
    help = 'Seed initial data for the application'

    def add_arguments(self, parser):
        parser.add_argument(
            '--with-test-users',
            action='store_true',
            help='Include test users (development only)',
        )

    def handle(self, *args, **options):
        self.stdout.write('Seeding data...')

        # Create admin if not exists
        self._create_admin()

        # Create subjects
        self._create_subjects()

        # Create levels
        self._create_levels()

        # Link subjects with levels
        self._create_subject_levels()

        # Create rooms
        self._create_rooms()

        # Create test users if requested
        if options['with_test_users']:
            self._create_test_users()

        self.stdout.write(self.style.SUCCESS('Seeding completed!'))

    def _create_admin(self):
        if not User.objects.filter(email='admin@napiatke.pl').exists():
            User.objects.create_superuser(
                email='admin@napiatke.pl',
                password='admin123',
                first_name='Admin',
                last_name='System',
            )
            self.stdout.write('  Created admin user')

    def _create_subjects(self):
        subjects = [
            {'name': 'Matematyka', 'icon': 'calculator', 'color': '#3B82F6'},
            {'name': 'Język Polski', 'icon': 'book', 'color': '#EF4444'},
            {'name': 'Język Angielski', 'icon': 'globe', 'color': '#10B981'},
            {'name': 'Fizyka', 'icon': 'atom', 'color': '#8B5CF6'},
            {'name': 'Chemia', 'icon': 'flask', 'color': '#F59E0B'},
            {'name': 'Biologia', 'icon': 'leaf', 'color': '#22C55E'},
            {'name': 'Historia', 'icon': 'landmark', 'color': '#6366F1'},
            {'name': 'Geografia', 'icon': 'map', 'color': '#14B8A6'},
        ]
        for data in subjects:
            Subject.objects.get_or_create(name=data['name'], defaults=data)
        self.stdout.write(f'  Created {len(subjects)} subjects')

    def _create_levels(self):
        levels = [
            {'name': 'Klasa 1-3', 'order_index': 1, 'color': '#10B981'},
            {'name': 'Klasa 4-6', 'order_index': 2, 'color': '#3B82F6'},
            {'name': 'Klasa 7-8', 'order_index': 3, 'color': '#8B5CF6'},
            {'name': 'Liceum', 'order_index': 4, 'color': '#EF4444'},
            {'name': 'Matura', 'order_index': 5, 'color': '#F59E0B'},
        ]
        for data in levels:
            Level.objects.get_or_create(name=data['name'], defaults=data)
        self.stdout.write(f'  Created {len(levels)} levels')

    def _create_subject_levels(self):
        subjects = Subject.objects.all()
        levels = Level.objects.all()
        count = 0
        for subject in subjects:
            for level in levels:
                _, created = SubjectLevel.objects.get_or_create(
                    subject=subject,
                    level=level,
                )
                if created:
                    count += 1
        self.stdout.write(f'  Created {count} subject-level links')

    def _create_rooms(self):
        rooms = [
            {
                'name': 'Sala 1',
                'capacity': 6,
                'location': 'Parter',
                'equipment': {'whiteboard': True, 'projector': True},
            },
            {
                'name': 'Sala 2',
                'capacity': 4,
                'location': 'Pierwsze piętro',
                'equipment': {'whiteboard': True, 'computers': True},
            },
            {
                'name': 'Sala 3',
                'capacity': 8,
                'location': 'Parter',
                'equipment': {'whiteboard': True, 'projector': True},
            },
            {
                'name': 'Online',
                'capacity': 20,
                'location': 'Wirtualna',
                'is_virtual': True,
                'equipment': {'video': True, 'screen_share': True},
            },
        ]
        for data in rooms:
            Room.objects.get_or_create(name=data['name'], defaults=data)
        self.stdout.write(f'  Created {len(rooms)} rooms')

    def _create_test_users(self):
        from apps.tutors.models import TutorProfile
        from apps.students.models import StudentProfile

        # Test tutor
        tutor, created = User.objects.get_or_create(
            email='tutor@test.pl',
            defaults={
                'first_name': 'Jan',
                'last_name': 'Kowalski',
                'role': 'tutor',
                'is_profile_completed': True,
                'first_login': False,
            },
        )
        if created:
            tutor.set_password('test123')
            tutor.save()
            TutorProfile.objects.create(
                user=tutor,
                bio='Doświadczony nauczyciel matematyki',
                hourly_rate=45.00,
                experience_years=8,
                is_verified=True,
            )
            self.stdout.write('  Created test tutor')

        # Test student
        student, created = User.objects.get_or_create(
            email='student@test.pl',
            defaults={
                'first_name': 'Anna',
                'last_name': 'Nowak',
                'role': 'student',
                'is_profile_completed': True,
                'first_login': False,
            },
        )
        if created:
            student.set_password('test123')
            student.save()
            StudentProfile.objects.create(
                user=student,
                class_name='7A',
                parent_name='Katarzyna Nowak',
                parent_phone='+48123456789',
                parent_email='rodzic@test.pl',
            )
            self.stdout.write('  Created test student')
```

**Execute seed command**:

```bash
# Basic seed (subjects, levels, rooms)
python manage.py seed_data

# With test users (development only)
python manage.py seed_data --with-test-users
```

---

## COMPLETION CHECKLIST

### Technical Validation

- [ ] All models created in correct apps
- [ ] All relationships working correctly
- [ ] All indexes defined
- [ ] Migrations run without errors
- [ ] Seed data populates correctly
- [ ] Django Admin shows all models
- [ ] Database constraints enforced
- [ ] Foreign key relationships validated

### Data Integrity

- [ ] User roles properly constrained
- [ ] Email uniqueness enforced
- [ ] Required fields cannot be null
- [ ] TextChoices values match specification
- [ ] Timestamps auto-populated
- [ ] UUIDs generated correctly (if using)

### Development Readiness

- [ ] All models registered in admin
- [ ] QuerySets and Managers implemented
- [ ] Seed command works correctly
- [ ] Test data available in development
- [ ] Database reset capability (migrate --run-syncdb)

---

## TROUBLESHOOTING

### Migration Issues

```bash
# Reset all migrations
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -path "*/migrations/*.pyc" -delete

# Drop and recreate database
docker-compose down -v
docker-compose up -d

# Recreate migrations
python manage.py makemigrations
python manage.py migrate
```

### Circular Import Issues

```python
# Use string references for ForeignKey
class Lesson(models.Model):
    subject = models.ForeignKey(
        'subjects.Subject',  # String reference
        on_delete=models.PROTECT,
    )
```

---

## SUCCESS METRICS

| Metric | Target |
|--------|--------|
| Schema Completeness | 100% of required models |
| Relationship Integrity | All foreign keys working |
| Performance | All queries <50ms |
| Data Quality | All constraints enforced |
| Development Speed | Team can start feature development immediately |

---

**Sprint Completion**: All 8 tasks completed and validated
**Next Sprint**: 1.2 - Authentication System Implementation
