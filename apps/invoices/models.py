import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone


class InvoiceStatus(models.TextChoices):
    GENERATED = 'GENERATED', 'Wygenerowana'
    SENT = 'SENT', 'Wysłana'
    PAID = 'PAID', 'Opłacona'
    OVERDUE = 'OVERDUE', 'Zaległa'
    CANCELLED = 'CANCELLED', 'Anulowana'
    CORRECTED = 'CORRECTED', 'Skorygowana'


class Invoice(models.Model):
    """Invoice model for student billing."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice_number = models.CharField('Numer faktury', max_length=50, unique=True)
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='invoices',
        verbose_name='Uczeń',
    )
    month_year = models.CharField('Miesiąc', max_length=7)  # YYYY-MM format

    net_amount = models.DecimalField(
        'Kwota netto',
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
    )
    vat_amount = models.DecimalField(
        'Kwota VAT',
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
    )
    total_amount = models.DecimalField(
        'Kwota brutto',
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
    )

    status = models.CharField(
        'Status',
        max_length=20,
        choices=InvoiceStatus.choices,
        default=InvoiceStatus.GENERATED,
    )
    issue_date = models.DateField('Data wystawienia')
    due_date = models.DateField('Termin płatności')
    paid_date = models.DateField('Data płatności', null=True, blank=True)
    pdf_path = models.CharField('Ścieżka PDF', max_length=255, blank=True)
    notes = models.TextField('Notatki', blank=True)

    created_at = models.DateTimeField('Utworzono', auto_now_add=True)
    updated_at = models.DateTimeField('Zaktualizowano', auto_now=True)

    class Meta:
        db_table = 'invoices'
        verbose_name = 'Faktura'
        verbose_name_plural = 'Faktury'
        ordering = ['-issue_date']
        indexes = [
            models.Index(fields=['student']),
            models.Index(fields=['month_year']),
            models.Index(fields=['status']),
            models.Index(fields=['issue_date']),
            models.Index(fields=['due_date']),
        ]

    def __str__(self):
        return f"{self.invoice_number} - {self.student.get_full_name()}"

    @property
    def is_overdue(self) -> bool:
        """Check if invoice is overdue."""
        if self.status == InvoiceStatus.PAID:
            return False
        return timezone.now().date() > self.due_date


class InvoiceItem(models.Model):
    """Invoice line item."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Faktura',
    )
    lesson = models.ForeignKey(
        'lessons.Lesson',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoice_items',
        verbose_name='Lekcja',
    )
    description = models.CharField('Opis', max_length=500)
    quantity = models.DecimalField('Ilość', max_digits=5, decimal_places=2)
    unit_price = models.DecimalField('Cena jednostkowa', max_digits=10, decimal_places=2)
    total_price = models.DecimalField('Wartość', max_digits=10, decimal_places=2)

    created_at = models.DateTimeField('Utworzono', auto_now_add=True)

    class Meta:
        db_table = 'invoice_items'
        verbose_name = 'Pozycja faktury'
        verbose_name_plural = 'Pozycje faktur'
        indexes = [
            models.Index(fields=['invoice']),
            models.Index(fields=['lesson']),
        ]

    def __str__(self):
        return f"{self.description} - {self.total_price} PLN"
