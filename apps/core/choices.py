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
