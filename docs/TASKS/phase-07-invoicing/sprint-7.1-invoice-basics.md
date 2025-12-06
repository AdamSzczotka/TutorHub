# Phase 7 - Sprint 7.1: Invoice Basics (Django)

## Tasks 087-091: Invoice Models & PDF Generation

> **Duration**: Week 11 (First half of Phase 7)
> **Goal**: Complete invoice foundation with models, calculations, and PDF templates
> **Dependencies**: Phase 6 completed (Cancellation & makeup system)

---

## SPRINT OVERVIEW

| Task ID | Description                       | Priority | Dependencies     |
| ------- | --------------------------------- | -------- | ---------------- |
| 087     | Invoice & InvoiceItem models      | Critical | Phase 6 complete |
| 088     | InvoiceService implementation     | Critical | Task 087         |
| 089     | Tax calculations (VAT 23%)        | Critical | Task 088         |
| 090     | Invoice numbering (FV/YYYY/MM/NN) | Critical | Task 089         |
| 091     | Invoice PDF templates (WeasyPrint)| Critical | Task 090         |

---

## INVOICE MODELS

**File**: `apps/invoices/models.py`

```python
from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import uuid


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
        related_name='invoices'
    )
    month_year = models.CharField('Miesiąc', max_length=7)  # YYYY-MM format

    net_amount = models.DecimalField('Kwota netto', max_digits=10, decimal_places=2)
    vat_amount = models.DecimalField('Kwota VAT', max_digits=10, decimal_places=2)
    total_amount = models.DecimalField('Kwota brutto', max_digits=10, decimal_places=2)

    status = models.CharField(
        'Status',
        max_length=20,
        choices=InvoiceStatus.choices,
        default=InvoiceStatus.GENERATED
    )
    issue_date = models.DateField('Data wystawienia')
    due_date = models.DateField('Termin płatności')
    paid_date = models.DateField('Data płatności', null=True, blank=True)
    pdf_path = models.CharField('Ścieżka PDF', max_length=255, blank=True)
    notes = models.TextField('Notatki', blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'invoices'
        verbose_name = 'Faktura'
        verbose_name_plural = 'Faktury'
        ordering = ['-issue_date']

    def __str__(self):
        return f"{self.invoice_number} - {self.student.get_full_name()}"


class InvoiceItem(models.Model):
    """Invoice line item."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='items'
    )
    lesson = models.ForeignKey(
        'lessons.Lesson',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoice_items'
    )
    description = models.CharField('Opis', max_length=500)
    quantity = models.DecimalField('Ilość', max_digits=5, decimal_places=2)
    unit_price = models.DecimalField('Cena jednostkowa', max_digits=10, decimal_places=2)
    total_price = models.DecimalField('Wartość', max_digits=10, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'invoice_items'
        verbose_name = 'Pozycja faktury'
        verbose_name_plural = 'Pozycje faktur'

    def __str__(self):
        return f"{self.description} - {self.total_price} PLN"
```

---

## TAX UTILITIES

**File**: `apps/invoices/utils.py`

```python
from decimal import Decimal, ROUND_HALF_UP

# VAT rates for Poland
VAT_STANDARD = Decimal('0.23')  # 23%
VAT_REDUCED = Decimal('0.08')   # 8%
VAT_ZERO = Decimal('0.00')      # 0%


def round_currency(value):
    """Round to 2 decimal places for currency."""
    return Decimal(value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def calculate_vat_from_net(net_amount, vat_rate=VAT_STANDARD):
    """Calculate VAT from net amount."""
    net = Decimal(str(net_amount))
    vat = net * vat_rate
    gross = net + vat

    return {
        'net_amount': round_currency(net),
        'vat_amount': round_currency(vat),
        'gross_amount': round_currency(gross),
        'vat_rate': vat_rate,
    }


def calculate_vat_from_gross(gross_amount, vat_rate=VAT_STANDARD):
    """Calculate VAT from gross amount."""
    gross = Decimal(str(gross_amount))
    net = gross / (1 + vat_rate)
    vat = gross - net

    return {
        'net_amount': round_currency(net),
        'vat_amount': round_currency(vat),
        'gross_amount': round_currency(gross),
        'vat_rate': vat_rate,
    }


def format_currency(amount):
    """Format amount as Polish currency."""
    amount = Decimal(str(amount))
    return f"{amount:,.2f} zł".replace(',', ' ').replace('.', ',')


def amount_to_words(amount):
    """Convert amount to Polish words."""
    units = ['', 'jeden', 'dwa', 'trzy', 'cztery', 'pięć', 'sześć', 'siedem', 'osiem', 'dziewięć']
    teens = ['dziesięć', 'jedenaście', 'dwanaście', 'trzynaście', 'czternaście',
             'piętnaście', 'szesnaście', 'siedemnaście', 'osiemnaście', 'dziewiętnaście']
    tens = ['', '', 'dwadzieścia', 'trzydzieści', 'czterdzieści', 'pięćdziesiąt',
            'sześćdziesiąt', 'siedemdziesiąt', 'osiemdziesiąt', 'dziewięćdziesiąt']
    hundreds = ['', 'sto', 'dwieście', 'trzysta', 'czterysta', 'pięćset',
                'sześćset', 'siedemset', 'osiemset', 'dziewięćset']

    amount = Decimal(str(amount))
    zlote, grosze = str(amount.quantize(Decimal('0.01'))).split('.')
    zlote_num = int(zlote)

    if zlote_num == 0:
        return f"zero złotych {grosze}/100"

    def convert_hundreds(num):
        result = ''
        h = num // 100
        t = (num % 100) // 10
        u = num % 10

        if h > 0:
            result += hundreds[h] + ' '

        if t == 1:
            result += teens[u] + ' '
        else:
            if t > 0:
                result += tens[t] + ' '
            if u > 0:
                result += units[u] + ' '

        return result

    result = ''

    # Thousands
    if zlote_num >= 1000:
        thousands = zlote_num // 1000
        result += convert_hundreds(thousands)
        if thousands == 1:
            result += 'tysiąc '
        elif 2 <= thousands % 10 <= 4 and not (12 <= thousands % 100 <= 14):
            result += 'tysiące '
        else:
            result += 'tysięcy '

    # Hundreds
    remainder = zlote_num % 1000
    if remainder > 0:
        result += convert_hundreds(remainder)

    # Currency suffix
    if zlote_num == 1:
        result += 'złoty'
    elif 2 <= zlote_num % 10 <= 4 and not (12 <= zlote_num % 100 <= 14):
        result += 'złote'
    else:
        result += 'złotych'

    result += f' {grosze}/100'

    return result.strip()
```

---

## INVOICE SERVICE

**File**: `apps/invoices/services.py`

```python
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import datetime
from dateutil.relativedelta import relativedelta

from .models import Invoice, InvoiceItem, InvoiceStatus
from .utils import round_currency, VAT_STANDARD


class InvoiceService:
    """Service for invoice management."""

    VAT_RATE = VAT_STANDARD

    def calculate_item_total(self, quantity, unit_price):
        """Calculate line item total."""
        total = Decimal(str(quantity)) * Decimal(str(unit_price))
        return {
            'quantity': round_currency(quantity),
            'unit_price': round_currency(unit_price),
            'total_price': round_currency(total),
        }

    def calculate_invoice_totals(self, items):
        """Calculate invoice totals with VAT."""
        net_amount = sum(item['total_price'] for item in items)
        vat_amount = net_amount * self.VAT_RATE
        total_amount = net_amount + vat_amount

        return {
            'net_amount': round_currency(net_amount),
            'vat_amount': round_currency(vat_amount),
            'total_amount': round_currency(total_amount),
        }

    def calculate_items_for_month(self, student, month_year):
        """Calculate invoice items for student's monthly lessons."""
        from apps.lessons.models import Lesson

        year, month = map(int, month_year.split('-'))
        start_date = datetime(year, month, 1)
        end_date = start_date + relativedelta(months=1)

        # Get completed/scheduled lessons for the month
        lessons = Lesson.objects.filter(
            students=student,
            start_time__gte=start_date,
            start_time__lt=end_date,
            status__in=['SCHEDULED', 'COMPLETED']
        ).select_related('subject', 'tutor', 'tutor__tutor_profile')

        items = []
        for lesson in lessons:
            # Get hourly rate from tutor profile or default
            tutor_profile = getattr(lesson.tutor, 'tutor_profile', None)
            hourly_rate = tutor_profile.hourly_rate if tutor_profile else Decimal('100.00')

            # Calculate duration in hours
            duration = (lesson.end_time - lesson.start_time).total_seconds() / 3600
            duration = Decimal(str(duration))

            item_calc = self.calculate_item_total(duration, hourly_rate)

            items.append({
                'lesson': lesson,
                'description': f"{lesson.subject.name} ({lesson.start_time.strftime('%d.%m.%Y')})",
                **item_calc
            })

        return items

    @transaction.atomic
    def create_invoice(self, student, month_year, items, due_date, notes=''):
        """Create invoice for student."""
        # Calculate totals
        item_calculations = [
            self.calculate_item_total(item['quantity'], item['unit_price'])
            for item in items
        ]
        totals = self.calculate_invoice_totals(item_calculations)

        # Generate invoice number
        invoice_number = self.generate_invoice_number(month_year)

        # Create invoice
        invoice = Invoice.objects.create(
            invoice_number=invoice_number,
            student=student,
            month_year=month_year,
            net_amount=totals['net_amount'],
            vat_amount=totals['vat_amount'],
            total_amount=totals['total_amount'],
            status=InvoiceStatus.GENERATED,
            issue_date=timezone.now().date(),
            due_date=due_date,
            notes=notes
        )

        # Create invoice items
        for i, item in enumerate(items):
            InvoiceItem.objects.create(
                invoice=invoice,
                lesson=item.get('lesson'),
                description=item['description'],
                quantity=item_calculations[i]['quantity'],
                unit_price=item_calculations[i]['unit_price'],
                total_price=item_calculations[i]['total_price']
            )

        return invoice

    def generate_invoice_number(self, month_year):
        """Generate sequential invoice number (FV/YYYY/MM/NNN)."""
        year, month = month_year.split('-')

        # Find last invoice for this month
        prefix = f"FV/{year}/{month}/"
        last_invoice = Invoice.objects.filter(
            invoice_number__startswith=prefix
        ).order_by('-invoice_number').first()

        if last_invoice:
            last_num = int(last_invoice.invoice_number.split('/')[-1])
            sequence = last_num + 1
        else:
            sequence = 1

        return f"{prefix}{str(sequence).zfill(3)}"

    def update_status(self, invoice_id, status, paid_date=None, notes=None):
        """Update invoice status."""
        invoice = Invoice.objects.get(id=invoice_id)
        invoice.status = status

        if paid_date:
            invoice.paid_date = paid_date
        if notes:
            invoice.notes = notes

        invoice.save()
        return invoice

    def get_by_id(self, invoice_id):
        """Get invoice with all relations."""
        return Invoice.objects.select_related(
            'student',
            'student__student_profile'
        ).prefetch_related(
            'items',
            'items__lesson',
            'items__lesson__subject'
        ).get(id=invoice_id)


invoice_service = InvoiceService()
```

---

## COMPANY CONFIGURATION

**File**: `apps/invoices/company_config.py`

```python
COMPANY_DETAILS = {
    'name': 'Na Piątkę - Szkoła Korepetycji',
    'address': 'ul. Edukacyjna 123',
    'city': 'Warszawa',
    'postal_code': '00-001',
    'nip': '1234567890',
    'regon': '123456789',
    'phone': '+48 123 456 789',
    'email': 'kontakt@napiatke.pl',
    'website': 'www.napiatke.pl',
    'bank_account': 'PL 12 3456 7890 1234 5678 9012 3456',
    'bank_name': 'Bank Example SA',
}
```

---

## PDF SERVICE (WeasyPrint)

**File**: `apps/invoices/pdf_service.py`

```python
from django.template.loader import render_to_string
from django.conf import settings
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
from io import BytesIO
from pathlib import Path
import os

from .utils import format_currency, amount_to_words
from .company_config import COMPANY_DETAILS


class InvoicePDFService:
    """Service for generating invoice PDFs."""

    def generate_pdf(self, invoice):
        """Generate PDF for invoice."""
        # Prepare context
        context = {
            'invoice': invoice,
            'company': COMPANY_DETAILS,
            'amount_in_words': amount_to_words(invoice.total_amount),
            'format_currency': format_currency,
        }

        # Render HTML
        html_content = render_to_string(
            'invoices/pdf/invoice.html',
            context
        )

        # CSS styling
        css = CSS(string=self._get_styles())

        # Generate PDF
        font_config = FontConfiguration()
        html = HTML(string=html_content)
        pdf_buffer = BytesIO()
        html.write_pdf(pdf_buffer, stylesheets=[css], font_config=font_config)
        pdf_buffer.seek(0)

        return pdf_buffer

    def save_pdf(self, invoice, upload_to_cloud=False):
        """Generate and save PDF to filesystem or cloud."""
        pdf_buffer = self.generate_pdf(invoice)

        filename = f"{invoice.invoice_number.replace('/', '-')}.pdf"

        if upload_to_cloud and hasattr(settings, 'AWS_S3_BUCKET'):
            # S3 upload (optional for production)
            pdf_url = self._upload_to_s3(pdf_buffer, filename)
        else:
            # Local storage
            invoices_dir = Path(settings.MEDIA_ROOT) / 'invoices'
            invoices_dir.mkdir(parents=True, exist_ok=True)

            filepath = invoices_dir / filename
            with open(filepath, 'wb') as f:
                f.write(pdf_buffer.getvalue())

            pdf_url = f"/media/invoices/{filename}"

        # Update invoice with PDF path
        invoice.pdf_path = pdf_url
        invoice.save()

        return pdf_url

    def _upload_to_s3(self, pdf_buffer, filename):
        """Upload PDF to S3 (optional)."""
        import boto3

        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )

        bucket = settings.AWS_S3_BUCKET
        key = f"invoices/{filename}"

        s3_client.put_object(
            Bucket=bucket,
            Key=key,
            Body=pdf_buffer.getvalue(),
            ContentType='application/pdf'
        )

        return f"https://{bucket}.s3.amazonaws.com/{key}"

    def _get_styles(self):
        """Get CSS styles for PDF."""
        return '''
            @page {
                size: A4;
                margin: 2cm;
            }
            body {
                font-family: 'DejaVu Sans', sans-serif;
                font-size: 10pt;
                line-height: 1.4;
                color: #333;
            }
            .header {
                border-bottom: 2px solid #3B82F6;
                padding-bottom: 10px;
                margin-bottom: 20px;
            }
            .title {
                font-size: 24pt;
                font-weight: bold;
                color: #1F2937;
                margin: 0;
            }
            .invoice-number {
                font-size: 12pt;
                color: #6B7280;
                margin-top: 5px;
            }
            .parties {
                display: flex;
                justify-content: space-between;
                margin-bottom: 30px;
            }
            .party {
                width: 45%;
            }
            .party-title {
                font-size: 11pt;
                font-weight: bold;
                color: #1F2937;
                margin-bottom: 8px;
                border-bottom: 1px solid #E5E7EB;
                padding-bottom: 5px;
            }
            .party-info {
                font-size: 9pt;
                line-height: 1.6;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }
            th {
                background-color: #3B82F6;
                color: white;
                padding: 10px 8px;
                text-align: left;
                font-size: 9pt;
                font-weight: bold;
            }
            td {
                padding: 10px 8px;
                border-bottom: 1px solid #E5E7EB;
                font-size: 9pt;
            }
            .text-right {
                text-align: right;
            }
            .summary {
                margin-top: 20px;
                text-align: right;
            }
            .summary-row {
                display: flex;
                justify-content: flex-end;
                margin-bottom: 5px;
            }
            .summary-label {
                width: 150px;
                text-align: left;
            }
            .summary-value {
                width: 120px;
                text-align: right;
                font-weight: bold;
            }
            .summary-total {
                border-top: 2px solid #1F2937;
                padding-top: 10px;
                margin-top: 10px;
                font-size: 14pt;
            }
            .amount-words {
                background-color: #F9FAFB;
                padding: 15px;
                margin: 20px 0;
                border-radius: 5px;
            }
            .payment-info {
                margin-top: 30px;
                padding: 15px;
                background-color: #EFF6FF;
                border-radius: 5px;
            }
            .payment-title {
                font-weight: bold;
                margin-bottom: 10px;
            }
            .footer {
                position: fixed;
                bottom: 0;
                left: 0;
                right: 0;
                text-align: center;
                font-size: 8pt;
                color: #9CA3AF;
                border-top: 1px solid #E5E7EB;
                padding-top: 10px;
            }
        '''


pdf_service = InvoicePDFService()
```

---

## PDF TEMPLATE

**File**: `templates/invoices/pdf/invoice.html`

```html
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <title>Faktura {{ invoice.invoice_number }}</title>
</head>
<body>
    <!-- Header -->
    <div class="header">
        <h1 class="title">FAKTURA VAT</h1>
        <div class="invoice-number">Nr {{ invoice.invoice_number }}</div>
        <div style="margin-top: 10px; font-size: 9pt;">
            Data wystawienia: {{ invoice.issue_date|date:"d.m.Y" }}<br>
            Termin płatności: {{ invoice.due_date|date:"d.m.Y" }}
        </div>
    </div>

    <!-- Parties -->
    <div class="parties">
        <!-- Seller -->
        <div class="party">
            <div class="party-title">Sprzedawca:</div>
            <div class="party-info">
                <strong>{{ company.name }}</strong><br>
                {{ company.address }}<br>
                {{ company.postal_code }} {{ company.city }}<br>
                NIP: {{ company.nip }}<br>
                {% if company.regon %}REGON: {{ company.regon }}<br>{% endif %}
                Tel: {{ company.phone }}<br>
                Email: {{ company.email }}
            </div>
        </div>

        <!-- Buyer -->
        <div class="party">
            <div class="party-title">Nabywca:</div>
            <div class="party-info">
                {% if invoice.student.student_profile.parent_name %}
                <strong>{{ invoice.student.student_profile.parent_name }}</strong><br>
                {% else %}
                <strong>{{ invoice.student.get_full_name }}</strong><br>
                {% endif %}
                {{ invoice.student.student_profile.parent_email|default:invoice.student.email }}
            </div>
        </div>
    </div>

    <!-- Items Table -->
    <table>
        <thead>
            <tr>
                <th style="width: 5%;">Lp.</th>
                <th style="width: 40%;">Nazwa usługi</th>
                <th style="width: 12%;" class="text-right">Ilość (h)</th>
                <th style="width: 15%;" class="text-right">Cena netto</th>
                <th style="width: 15%;" class="text-right">Wartość netto</th>
                <th style="width: 8%;" class="text-right">VAT</th>
            </tr>
        </thead>
        <tbody>
            {% for item in invoice.items.all %}
            <tr>
                <td>{{ forloop.counter }}</td>
                <td>{{ item.description }}</td>
                <td class="text-right">{{ item.quantity }}</td>
                <td class="text-right">{{ item.unit_price|floatformat:2 }} zł</td>
                <td class="text-right">{{ item.total_price|floatformat:2 }} zł</td>
                <td class="text-right">23%</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

    <!-- Summary -->
    <div class="summary">
        <div class="summary-row">
            <span class="summary-label">Suma netto:</span>
            <span class="summary-value">{{ invoice.net_amount|floatformat:2 }} zł</span>
        </div>
        <div class="summary-row">
            <span class="summary-label">VAT (23%):</span>
            <span class="summary-value">{{ invoice.vat_amount|floatformat:2 }} zł</span>
        </div>
        <div class="summary-row summary-total">
            <span class="summary-label">RAZEM BRUTTO:</span>
            <span class="summary-value">{{ invoice.total_amount|floatformat:2 }} zł</span>
        </div>
    </div>

    <!-- Amount in Words -->
    <div class="amount-words">
        <strong>Słownie:</strong> {{ amount_in_words }}
    </div>

    <!-- Payment Info -->
    <div class="payment-info">
        <div class="payment-title">Forma płatności: Przelew bankowy</div>
        <div>Numer konta: {{ company.bank_account }}</div>
        <div>Bank: {{ company.bank_name }}</div>
        <div style="margin-top: 10px;">
            <strong>Tytuł przelewu:</strong> {{ invoice.invoice_number }}
        </div>
    </div>

    {% if invoice.notes %}
    <div style="margin-top: 20px;">
        <strong>Uwagi:</strong><br>
        {{ invoice.notes }}
    </div>
    {% endif %}

    <!-- Footer -->
    <div class="footer">
        {{ company.name }} | {{ company.address }}, {{ company.postal_code }} {{ company.city }} |
        NIP: {{ company.nip }} | Tel: {{ company.phone }} | Email: {{ company.email }}
    </div>
</body>
</html>
```

---

## INVOICE VIEWS

**File**: `apps/invoices/views.py`

```python
from django.views.generic import ListView, DetailView, View, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, FileResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from io import BytesIO

from apps.core.mixins import AdminRequiredMixin, HTMXMixin
from .models import Invoice, InvoiceStatus
from .services import invoice_service
from .pdf_service import pdf_service


class InvoiceListView(LoginRequiredMixin, HTMXMixin, ListView):
    """Display invoice list."""
    template_name = 'invoices/list.html'
    partial_template_name = 'invoices/partials/_invoice_list.html'
    context_object_name = 'invoices'
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user
        queryset = Invoice.objects.select_related('student')

        # Students see only their invoices
        if user.role == 'STUDENT':
            queryset = queryset.filter(student=user)

        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        # Filter by month
        month_year = self.request.GET.get('month_year')
        if month_year:
            queryset = queryset.filter(month_year=month_year)

        return queryset.order_by('-issue_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_status'] = self.request.GET.get('status', '')
        context['statuses'] = InvoiceStatus.choices
        return context


class InvoiceDetailView(LoginRequiredMixin, HTMXMixin, DetailView):
    """Display invoice details."""
    template_name = 'invoices/detail.html'
    partial_template_name = 'invoices/partials/_invoice_detail.html'
    context_object_name = 'invoice'

    def get_queryset(self):
        user = self.request.user
        queryset = Invoice.objects.select_related(
            'student', 'student__student_profile'
        ).prefetch_related('items', 'items__lesson', 'items__lesson__subject')

        if user.role == 'STUDENT':
            queryset = queryset.filter(student=user)

        return queryset


class DownloadInvoicePDFView(LoginRequiredMixin, View):
    """Download invoice PDF."""

    def get(self, request, pk):
        invoice = get_object_or_404(Invoice, id=pk)

        # Permission check
        if request.user.role == 'STUDENT' and invoice.student != request.user:
            return HttpResponse("Brak uprawnień", status=403)

        # Generate PDF
        pdf_buffer = pdf_service.generate_pdf(invoice)

        filename = f"{invoice.invoice_number.replace('/', '-')}.pdf"

        return FileResponse(
            pdf_buffer,
            as_attachment=True,
            filename=filename,
            content_type='application/pdf'
        )


# Admin Views
class AdminInvoiceCreateView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    """Admin view to create invoice."""
    template_name = 'admin_panel/invoices/create.html'


class AdminCalculateInvoiceView(LoginRequiredMixin, AdminRequiredMixin, View):
    """Calculate invoice items for student/month."""

    def get(self, request):
        from apps.accounts.models import User

        student_id = request.GET.get('student_id')
        month_year = request.GET.get('month_year')

        if not student_id or not month_year:
            return HttpResponse(
                '<div class="alert alert-error">Wybierz ucznia i miesiąc.</div>',
                status=400
            )

        student = get_object_or_404(User, id=student_id, role='STUDENT')
        items = invoice_service.calculate_items_for_month(student, month_year)

        if not items:
            return HttpResponse(
                '<div class="alert alert-warning">Brak zajęć do zafakturowania w wybranym miesiącu.</div>'
            )

        totals = invoice_service.calculate_invoice_totals([
            invoice_service.calculate_item_total(item['quantity'], item['unit_price'])
            for item in items
        ])

        return render(request, 'admin_panel/invoices/partials/_calculated_items.html', {
            'items': items,
            'totals': totals,
            'student': student,
            'month_year': month_year,
        })


class AdminCreateInvoiceView(LoginRequiredMixin, AdminRequiredMixin, View):
    """Create invoice from calculated items."""

    def post(self, request):
        from apps.accounts.models import User
        from datetime import timedelta

        student_id = request.POST.get('student_id')
        month_year = request.POST.get('month_year')

        student = get_object_or_404(User, id=student_id)
        items = invoice_service.calculate_items_for_month(student, month_year)

        if not items:
            return HttpResponse(
                '<div class="alert alert-error">Brak pozycji do zafakturowania.</div>',
                status=400
            )

        # Calculate due date (14 days from now)
        due_date = timezone.now().date() + timedelta(days=14)

        invoice = invoice_service.create_invoice(
            student=student,
            month_year=month_year,
            items=items,
            due_date=due_date
        )

        return HttpResponse(
            f'''<div class="alert alert-success">
                Faktura {invoice.invoice_number} została utworzona.
                <a href="{{% url 'invoices:detail' invoice.id %}}" class="link">Zobacz</a>
            </div>''',
            headers={'HX-Trigger': 'invoiceCreated'}
        )


class AdminUpdateStatusView(LoginRequiredMixin, AdminRequiredMixin, View):
    """Update invoice status."""

    def post(self, request, pk):
        invoice = get_object_or_404(Invoice, id=pk)
        status = request.POST.get('status')
        paid_date = request.POST.get('paid_date')

        if status == 'PAID' and paid_date:
            from datetime import datetime
            paid_date = datetime.strptime(paid_date, '%Y-%m-%d').date()
        else:
            paid_date = None

        invoice_service.update_status(pk, status, paid_date)

        return HttpResponse(
            '<div class="alert alert-success">Status faktury zaktualizowany.</div>',
            headers={'HX-Trigger': 'statusUpdated'}
        )
```

---

## INVOICE TEMPLATES

**File**: `templates/invoices/list.html`

```html
{% extends "base.html" %}

{% block content %}
<div class="space-y-6">
    <div class="flex items-center justify-between">
        <div>
            <h1 class="text-2xl font-bold">Faktury</h1>
            <p class="text-base-content/70">Przeglądaj i pobieraj swoje faktury</p>
        </div>
    </div>

    <!-- Filters -->
    <div class="flex gap-4">
        <select class="select select-bordered"
                hx-get="{% url 'invoices:list' %}"
                hx-target="#invoice-list"
                hx-swap="innerHTML"
                hx-include="[name='month_year']"
                name="status">
            <option value="">Wszystkie statusy</option>
            {% for value, label in statuses %}
            <option value="{{ value }}" {% if current_status == value %}selected{% endif %}>{{ label }}</option>
            {% endfor %}
        </select>

        <input type="month"
               name="month_year"
               class="input input-bordered"
               hx-get="{% url 'invoices:list' %}"
               hx-target="#invoice-list"
               hx-swap="innerHTML"
               hx-include="[name='status']">
    </div>

    <div id="invoice-list">
        {% include "invoices/partials/_invoice_list.html" %}
    </div>
</div>
{% endblock %}
```

**File**: `templates/invoices/partials/_invoice_list.html`

```html
{% if invoices %}
<div class="overflow-x-auto">
    <table class="table table-zebra">
        <thead>
            <tr>
                <th>Numer</th>
                <th>Miesiąc</th>
                <th>Kwota brutto</th>
                <th>Status</th>
                <th>Termin</th>
                <th>Akcje</th>
            </tr>
        </thead>
        <tbody>
            {% for invoice in invoices %}
            <tr>
                <td class="font-medium">{{ invoice.invoice_number }}</td>
                <td>{{ invoice.month_year }}</td>
                <td class="font-bold">{{ invoice.total_amount|floatformat:2 }} zł</td>
                <td>
                    {% if invoice.status == 'PAID' %}
                    <span class="badge badge-success">Opłacona</span>
                    {% elif invoice.status == 'OVERDUE' %}
                    <span class="badge badge-error">Zaległa</span>
                    {% elif invoice.status == 'SENT' %}
                    <span class="badge badge-info">Wysłana</span>
                    {% else %}
                    <span class="badge badge-ghost">{{ invoice.get_status_display }}</span>
                    {% endif %}
                </td>
                <td>{{ invoice.due_date|date:"d.m.Y" }}</td>
                <td>
                    <div class="flex gap-2">
                        <a href="{% url 'invoices:detail' invoice.id %}"
                           class="btn btn-sm btn-ghost">
                            Szczegóły
                        </a>
                        <a href="{% url 'invoices:download_pdf' invoice.id %}"
                           class="btn btn-sm btn-primary"
                           download>
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                      d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
                            </svg>
                            PDF
                        </a>
                    </div>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>

{% if page_obj.has_other_pages %}
<div class="flex justify-center mt-4">
    <div class="btn-group">
        {% if page_obj.has_previous %}
        <a class="btn btn-sm" href="?page={{ page_obj.previous_page_number }}">«</a>
        {% endif %}
        <button class="btn btn-sm">Strona {{ page_obj.number }}</button>
        {% if page_obj.has_next %}
        <a class="btn btn-sm" href="?page={{ page_obj.next_page_number }}">»</a>
        {% endif %}
    </div>
</div>
{% endif %}

{% else %}
<div class="card bg-base-100 shadow">
    <div class="card-body py-12 text-center text-base-content/50">
        Brak faktur do wyświetlenia
    </div>
</div>
{% endif %}
```

---

## URL CONFIGURATION

**File**: `apps/invoices/urls.py`

```python
from django.urls import path
from . import views

app_name = 'invoices'

urlpatterns = [
    # Student/general views
    path('', views.InvoiceListView.as_view(), name='list'),
    path('<uuid:pk>/', views.InvoiceDetailView.as_view(), name='detail'),
    path('<uuid:pk>/download/', views.DownloadInvoicePDFView.as_view(), name='download_pdf'),

    # Admin views
    path('admin/create/', views.AdminInvoiceCreateView.as_view(), name='admin_create'),
    path('admin/calculate/', views.AdminCalculateInvoiceView.as_view(), name='admin_calculate'),
    path('admin/create/submit/', views.AdminCreateInvoiceView.as_view(), name='admin_create_submit'),
    path('admin/<uuid:pk>/status/', views.AdminUpdateStatusView.as_view(), name='admin_update_status'),
]
```

---

## REQUIREMENTS

**File**: `requirements/base.txt` (dodać)

```txt
# PDF generation
WeasyPrint>=60.0

# Date utilities
python-dateutil>=2.8.0

# AWS (optional for S3)
boto3>=1.26.0
```

---

## COMPLETION CHECKLIST

- [ ] Invoice model created with all fields
- [ ] InvoiceItem model created
- [ ] InvoiceService with calculations
- [ ] VAT 23% calculations accurate
- [ ] Invoice numbering FV/YYYY/MM/NNN
- [ ] PDF generation with WeasyPrint
- [ ] Polish characters rendering correctly
- [ ] Amount to words in Polish
- [ ] Company details configurable
- [ ] Admin create/view/status update
- [ ] Student can view/download own invoices
- [ ] HTMX interactions smooth

---

**Next Sprint**: 7.2 - Billing Cycle Automation
