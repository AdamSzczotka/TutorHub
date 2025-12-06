# Phase 7 - Sprint 7.2: Billing Cycle Automation (Django)

## Tasks 092-097: Monthly Billing & Payment Tracking

> **Duration**: Week 11 (Second half of Phase 7)
> **Goal**: Complete automated monthly billing system with payment tracking
> **Dependencies**: Sprint 7.1 completed (Invoice basics)

---

## SPRINT OVERVIEW

| Task ID | Description                            | Priority | Dependencies |
| ------- | -------------------------------------- | -------- | ------------ |
| 092     | Monthly billing automation (cron 25th) | Critical | Sprint 7.1   |
| 093     | PDF generation & email delivery        | Critical | Task 092     |
| 094     | Email queue with Celery                | Critical | Task 093     |
| 095     | Payment tracking                       | High     | Task 094     |
| 096     | Overdue management                     | High     | Task 095     |
| 097     | Correction notes                       | High     | Task 096     |

---

## BILLING SERVICE

**File**: `apps/invoices/services.py` (rozszerzenie)

```python
from django.utils import timezone
from django.db import transaction
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from dateutil.relativedelta import relativedelta
from datetime import timedelta

from .models import Invoice, InvoiceStatus
from .pdf_service import pdf_service


class BillingService:
    """Service for automated billing."""

    def generate_monthly_invoices(self, month_year=None):
        """Generate invoices for all active students for a given month."""
        from apps.accounts.models import User

        # Default to next month
        if month_year is None:
            target_date = timezone.now() + relativedelta(months=1)
            month_year = target_date.strftime('%Y-%m')

        # Get all active students
        active_students = User.objects.filter(
            role='STUDENT',
            is_active=True
        ).select_related('student_profile')

        results = {
            'success': [],
            'failed': [],
            'skipped': []
        }

        for student in active_students:
            try:
                result = self._generate_invoice_for_student(student, month_year)
                if result:
                    results['success'].append({
                        'student_id': str(student.id),
                        'invoice_number': result.invoice_number
                    })
                else:
                    results['skipped'].append({
                        'student_id': str(student.id),
                        'reason': 'No lessons or already exists'
                    })
            except Exception as e:
                results['failed'].append({
                    'student_id': str(student.id),
                    'error': str(e)
                })

        return results

    @transaction.atomic
    def _generate_invoice_for_student(self, student, month_year):
        """Generate invoice for single student."""
        from .services import invoice_service

        # Check if invoice already exists
        existing = Invoice.objects.filter(
            student=student,
            month_year=month_year
        ).exists()

        if existing:
            return None

        # Calculate items for month
        items = invoice_service.calculate_items_for_month(student, month_year)

        if not items:
            return None

        # Calculate due date (14 days into the month)
        year, month = map(int, month_year.split('-'))
        due_date = timezone.make_aware(
            timezone.datetime(year, month, 14)
        ).date()

        # Create invoice
        invoice = invoice_service.create_invoice(
            student=student,
            month_year=month_year,
            items=items,
            due_date=due_date,
            notes=f"Faktura automatyczna za {month_year}"
        )

        return invoice

    @transaction.atomic
    def generate_and_send_invoice(self, invoice_id):
        """Generate PDF and send invoice via email."""
        invoice = Invoice.objects.select_related(
            'student', 'student__student_profile'
        ).get(id=invoice_id)

        # Generate PDF
        pdf_url = pdf_service.save_pdf(invoice)

        # Update status
        invoice.status = InvoiceStatus.SENT
        invoice.pdf_path = pdf_url
        invoice.save()

        # Send email
        self._send_invoice_email(invoice)

        return {
            'pdf_path': pdf_url,
            'sent_to': self._get_recipient_email(invoice)
        }

    def send_all_pending_invoices(self, month_year):
        """Send all generated but not sent invoices for a month."""
        pending_invoices = Invoice.objects.filter(
            month_year=month_year,
            status=InvoiceStatus.GENERATED
        )

        results = {
            'success': [],
            'failed': []
        }

        for invoice in pending_invoices:
            try:
                self.generate_and_send_invoice(invoice.id)
                results['success'].append(str(invoice.id))
            except Exception as e:
                results['failed'].append({
                    'invoice_id': str(invoice.id),
                    'error': str(e)
                })

        return results

    def _send_invoice_email(self, invoice):
        """Send invoice email with PDF attachment."""
        from pathlib import Path

        recipient = self._get_recipient_email(invoice)
        student_name = invoice.student.get_full_name()

        context = {
            'invoice': invoice,
            'student_name': student_name,
            'month_name': self._get_month_name(invoice.month_year),
        }

        html_content = render_to_string(
            'emails/invoice_notification.html',
            context
        )

        email = EmailMessage(
            subject=f"Faktura {invoice.invoice_number} - Na Piątkę",
            body=html_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient]
        )
        email.content_subtype = 'html'

        # Attach PDF
        if invoice.pdf_path:
            if invoice.pdf_path.startswith('/media/'):
                pdf_path = Path(settings.MEDIA_ROOT) / invoice.pdf_path.replace('/media/', '')
                with open(pdf_path, 'rb') as f:
                    email.attach(
                        f"{invoice.invoice_number.replace('/', '-')}.pdf",
                        f.read(),
                        'application/pdf'
                    )

        email.send()

    def _get_recipient_email(self, invoice):
        """Get recipient email (parent or student)."""
        profile = getattr(invoice.student, 'student_profile', None)
        if profile and profile.parent_email:
            return profile.parent_email
        return invoice.student.email

    def _get_month_name(self, month_year):
        """Get Polish month name."""
        months = {
            '01': 'Styczeń', '02': 'Luty', '03': 'Marzec',
            '04': 'Kwiecień', '05': 'Maj', '06': 'Czerwiec',
            '07': 'Lipiec', '08': 'Sierpień', '09': 'Wrzesień',
            '10': 'Październik', '11': 'Listopad', '12': 'Grudzień'
        }
        year, month = month_year.split('-')
        return f"{months.get(month, month)} {year}"


billing_service = BillingService()
```

---

## OVERDUE SERVICE

**File**: `apps/invoices/services.py` (rozszerzenie)

```python
from django.utils import timezone
from datetime import timedelta


class OverdueService:
    """Service for managing overdue invoices."""

    def mark_overdue_invoices(self):
        """Mark invoices past due date as overdue."""
        today = timezone.now().date()

        overdue_invoices = Invoice.objects.filter(
            status__in=[InvoiceStatus.SENT, InvoiceStatus.GENERATED],
            due_date__lt=today
        )

        count = overdue_invoices.update(status=InvoiceStatus.OVERDUE)
        return count

    def send_payment_reminders(self):
        """Send reminders 7 days before due date."""
        from apps.core.models import AuditLog

        today = timezone.now().date()
        seven_days = today + timedelta(days=7)

        upcoming = Invoice.objects.filter(
            status__in=[InvoiceStatus.SENT, InvoiceStatus.GENERATED],
            due_date__gte=today,
            due_date__lte=seven_days
        ).select_related('student', 'student__student_profile')

        sent_count = 0
        for invoice in upcoming:
            # Check if reminder already sent today
            reminder_sent = AuditLog.objects.filter(
                model_type='Invoice',
                model_id=str(invoice.id),
                action='PAYMENT_REMINDER_SENT',
                created_at__date=today
            ).exists()

            if reminder_sent:
                continue

            self._send_reminder_email(invoice)

            # Log reminder
            AuditLog.objects.create(
                user=invoice.student,
                action='PAYMENT_REMINDER_SENT',
                model_type='Invoice',
                model_id=str(invoice.id)
            )

            sent_count += 1

        return sent_count

    def send_overdue_notices(self):
        """Send escalating overdue notices (1, 7, 14, 30 days)."""
        from apps.core.models import AuditLog

        today = timezone.now().date()

        overdue = Invoice.objects.filter(
            status=InvoiceStatus.OVERDUE
        ).select_related('student', 'student__student_profile')

        sent_count = 0
        for invoice in overdue:
            days_overdue = (today - invoice.due_date).days

            # Send at 1, 7, 14, 30 days
            if days_overdue not in [1, 7, 14, 30]:
                continue

            # Check if notice already sent today
            notice_sent = AuditLog.objects.filter(
                model_type='Invoice',
                model_id=str(invoice.id),
                action='OVERDUE_NOTICE_SENT',
                created_at__date=today
            ).exists()

            if notice_sent:
                continue

            self._send_overdue_email(invoice, days_overdue)

            # Log notice
            AuditLog.objects.create(
                user=invoice.student,
                action='OVERDUE_NOTICE_SENT',
                model_type='Invoice',
                model_id=str(invoice.id),
                new_values={'days_overdue': days_overdue}
            )

            sent_count += 1

        return sent_count

    def _send_reminder_email(self, invoice):
        """Send payment reminder email."""
        from django.core.mail import send_mail
        from .utils import format_currency

        recipient = billing_service._get_recipient_email(invoice)
        days_until = (invoice.due_date - timezone.now().date()).days

        context = {
            'student_name': invoice.student.get_full_name(),
            'invoice_number': invoice.invoice_number,
            'total_amount': format_currency(invoice.total_amount),
            'due_date': invoice.due_date.strftime('%d.%m.%Y'),
            'days_until': days_until,
        }

        html_content = render_to_string(
            'emails/payment_reminder.html',
            context
        )

        send_mail(
            subject=f"Przypomnienie o płatności - {invoice.invoice_number}",
            message='',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            html_message=html_content
        )

    def _send_overdue_email(self, invoice, days_overdue):
        """Send overdue notice email."""
        from django.core.mail import send_mail
        from .utils import format_currency

        recipient = billing_service._get_recipient_email(invoice)

        context = {
            'student_name': invoice.student.get_full_name(),
            'invoice_number': invoice.invoice_number,
            'total_amount': format_currency(invoice.total_amount),
            'due_date': invoice.due_date.strftime('%d.%m.%Y'),
            'days_overdue': days_overdue,
        }

        html_content = render_to_string(
            'emails/overdue_notice.html',
            context
        )

        send_mail(
            subject=f"ZALEGŁOŚĆ - Faktura {invoice.invoice_number}",
            message='',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            html_message=html_content
        )


overdue_service = OverdueService()
```

---

## CORRECTION SERVICE

**File**: `apps/invoices/services.py` (rozszerzenie)

```python
class CorrectionService:
    """Service for invoice corrections."""

    @transaction.atomic
    def create_credit_note(self, original_invoice, amount, reason):
        """Create credit note for invoice."""
        from .utils import round_currency, VAT_STANDARD

        now = timezone.now()
        year = now.year
        month = str(now.month).zfill(2)

        # Generate credit note number
        prefix = f"KOR/{year}/{month}/"
        last_credit = Invoice.objects.filter(
            invoice_number__startswith=prefix
        ).order_by('-invoice_number').first()

        if last_credit:
            last_num = int(last_credit.invoice_number.split('/')[-1])
            sequence = last_num + 1
        else:
            sequence = 1

        credit_number = f"{prefix}{str(sequence).zfill(3)}"

        # Calculate amounts (negative for credit)
        net_amount = -round_currency(amount)
        vat_amount = net_amount * VAT_STANDARD
        total_amount = net_amount + vat_amount

        # Create credit note
        credit_note = Invoice.objects.create(
            invoice_number=credit_number,
            student=original_invoice.student,
            month_year=original_invoice.month_year,
            net_amount=net_amount,
            vat_amount=vat_amount,
            total_amount=total_amount,
            status=InvoiceStatus.GENERATED,
            issue_date=now.date(),
            due_date=now.date(),
            notes=f"Korekta faktury {original_invoice.invoice_number}. Powód: {reason}"
        )

        # Update original invoice status
        original_invoice.status = InvoiceStatus.CORRECTED
        original_invoice.save()

        return credit_note


correction_service = CorrectionService()
```

---

## CELERY TASKS

**File**: `apps/invoices/tasks.py`

```python
from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


@shared_task
def monthly_billing_task(month_year=None):
    """Monthly billing automation task.

    Runs on 25th of each month at midnight.
    Generates invoices for next month and sends them.
    """
    from .services import billing_service
    from dateutil.relativedelta import relativedelta
    from django.utils import timezone

    if month_year is None:
        next_month = timezone.now() + relativedelta(months=1)
        month_year = next_month.strftime('%Y-%m')

    logger.info(f"Starting monthly billing for {month_year}")

    # Step 1: Generate invoices
    generate_results = billing_service.generate_monthly_invoices(month_year)

    logger.info(
        f"Generated: {len(generate_results['success'])}, "
        f"Failed: {len(generate_results['failed'])}, "
        f"Skipped: {len(generate_results['skipped'])}"
    )

    # Step 2: Send all generated invoices
    send_results = billing_service.send_all_pending_invoices(month_year)

    logger.info(
        f"Sent: {len(send_results['success'])}, "
        f"Failed to send: {len(send_results['failed'])}"
    )

    return {
        'month_year': month_year,
        'generated': len(generate_results['success']),
        'sent': len(send_results['success']),
        'failed': len(generate_results['failed']) + len(send_results['failed']),
        'skipped': len(generate_results['skipped'])
    }


@shared_task
def check_overdue_invoices_task():
    """Daily task to check and mark overdue invoices."""
    from .services import overdue_service

    # Mark overdue
    marked = overdue_service.mark_overdue_invoices()
    logger.info(f"Marked {marked} invoices as overdue")

    # Send reminders (7 days before due)
    reminders = overdue_service.send_payment_reminders()
    logger.info(f"Sent {reminders} payment reminders")

    # Send overdue notices
    notices = overdue_service.send_overdue_notices()
    logger.info(f"Sent {notices} overdue notices")

    return {
        'marked_overdue': marked,
        'reminders_sent': reminders,
        'notices_sent': notices
    }


@shared_task
def send_invoice_email_task(invoice_id):
    """Send single invoice email (queued)."""
    from .services import billing_service

    try:
        result = billing_service.generate_and_send_invoice(invoice_id)
        logger.info(f"Invoice {invoice_id} sent to {result['sent_to']}")
        return result
    except Exception as e:
        logger.error(f"Failed to send invoice {invoice_id}: {e}")
        raise


# Celery beat schedule (add to settings.py):
# CELERY_BEAT_SCHEDULE = {
#     'monthly-billing': {
#         'task': 'apps.invoices.tasks.monthly_billing_task',
#         'schedule': crontab(day_of_month=25, hour=0, minute=0),
#     },
#     'check-overdue-invoices': {
#         'task': 'apps.invoices.tasks.check_overdue_invoices_task',
#         'schedule': crontab(hour=8, minute=0),  # Daily at 8 AM
#     },
# }
```

---

## PAYMENT TRACKING VIEWS

**File**: `apps/invoices/views.py` (rozszerzenie)

```python
from django.views.generic import View, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from apps.core.mixins import AdminRequiredMixin, HTMXMixin
from .models import Invoice, InvoiceStatus
from .services import invoice_service, correction_service


class PaymentTrackerView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    """Admin view for payment tracking."""
    template_name = 'admin_panel/invoices/payment_tracker.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        invoice_id = self.kwargs.get('pk')
        context['invoice'] = get_object_or_404(Invoice, id=invoice_id)
        return context


class MarkAsPaidView(LoginRequiredMixin, AdminRequiredMixin, View):
    """Mark invoice as paid."""

    def post(self, request, pk):
        invoice = get_object_or_404(Invoice, id=pk)
        paid_date_str = request.POST.get('paid_date')

        from datetime import datetime

        if paid_date_str:
            paid_date = datetime.strptime(paid_date_str, '%Y-%m-%d').date()
        else:
            paid_date = timezone.now().date()

        invoice.status = InvoiceStatus.PAID
        invoice.paid_date = paid_date
        invoice.save()

        return HttpResponse(
            '''<div class="alert alert-success">
                Faktura została oznaczona jako opłacona.
            </div>''',
            headers={'HX-Trigger': 'invoiceUpdated'}
        )


class CreateCreditNoteView(LoginRequiredMixin, AdminRequiredMixin, View):
    """Create correction note for invoice."""

    def post(self, request, pk):
        invoice = get_object_or_404(Invoice, id=pk)
        amount = request.POST.get('amount')
        reason = request.POST.get('reason')

        if not amount or not reason:
            return HttpResponse(
                '<div class="alert alert-error">Wypełnij wszystkie pola.</div>',
                status=400
            )

        try:
            from decimal import Decimal
            amount = Decimal(amount)

            credit_note = correction_service.create_credit_note(
                invoice, amount, reason
            )

            return HttpResponse(
                f'''<div class="alert alert-success">
                    Nota korygująca {credit_note.invoice_number} została utworzona.
                </div>''',
                headers={'HX-Trigger': 'creditNoteCreated'}
            )
        except Exception as e:
            return HttpResponse(
                f'<div class="alert alert-error">{str(e)}</div>',
                status=400
            )


class AdminBillingDashboardView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    """Admin billing dashboard with statistics."""
    template_name = 'admin_panel/invoices/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Invoice statistics
        context['total_invoices'] = Invoice.objects.count()
        context['pending_count'] = Invoice.objects.filter(
            status__in=[InvoiceStatus.GENERATED, InvoiceStatus.SENT]
        ).count()
        context['paid_count'] = Invoice.objects.filter(
            status=InvoiceStatus.PAID
        ).count()
        context['overdue_count'] = Invoice.objects.filter(
            status=InvoiceStatus.OVERDUE
        ).count()

        # Total amounts
        from django.db.models import Sum

        context['total_outstanding'] = Invoice.objects.filter(
            status__in=[InvoiceStatus.SENT, InvoiceStatus.OVERDUE]
        ).aggregate(total=Sum('total_amount'))['total'] or 0

        context['total_paid'] = Invoice.objects.filter(
            status=InvoiceStatus.PAID
        ).aggregate(total=Sum('total_amount'))['total'] or 0

        # Recent invoices
        context['recent_invoices'] = Invoice.objects.select_related(
            'student'
        ).order_by('-created_at')[:10]

        return context


class TriggerMonthlyBillingView(LoginRequiredMixin, AdminRequiredMixin, View):
    """Manually trigger monthly billing."""

    def post(self, request):
        month_year = request.POST.get('month_year')

        if not month_year:
            return HttpResponse(
                '<div class="alert alert-error">Wybierz miesiąc.</div>',
                status=400
            )

        # Queue task
        from .tasks import monthly_billing_task
        monthly_billing_task.delay(month_year)

        return HttpResponse(
            f'''<div class="alert alert-success">
                Generowanie faktur dla {month_year} zostało zaplanowane.
                Sprawdź status w zakładce "Faktury".
            </div>'''
        )
```

---

## EMAIL TEMPLATES

**File**: `templates/emails/invoice_notification.html`

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: #3B82F6; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
            <h1 style="margin: 0; font-size: 24px;">Faktura {{ invoice.invoice_number }}</h1>
            <p style="margin: 5px 0 0 0; opacity: 0.9;">{{ month_name }}</p>
        </div>

        <div style="background: #fff; padding: 20px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 8px 8px;">
            <p>Dzień dobry,</p>

            <p>W załączeniu przesyłamy fakturę za korepetycje dla <strong>{{ student_name }}</strong>.</p>

            <div style="background: #f9fafb; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <p style="margin: 5px 0;"><strong>Numer faktury:</strong> {{ invoice.invoice_number }}</p>
                <p style="margin: 5px 0;"><strong>Kwota do zapłaty:</strong> {{ invoice.total_amount|floatformat:2 }} zł</p>
                <p style="margin: 5px 0;"><strong>Termin płatności:</strong> {{ invoice.due_date|date:"d.m.Y" }}</p>
            </div>

            <p>Prosimy o terminową płatność na podany na fakturze numer konta.</p>

            <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
                Pozdrawiamy,<br>
                Zespół "Na Piątkę"
            </p>
        </div>
    </div>
</body>
</html>
```

**File**: `templates/emails/payment_reminder.html`

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: #F59E0B; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
            <h1 style="margin: 0; font-size: 24px;">Przypomnienie o płatności</h1>
        </div>

        <div style="background: #fff; padding: 20px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 8px 8px;">
            <p>Dzień dobry,</p>

            <p>Przypominamy o zbliżającym się terminie płatności faktury.</p>

            <div style="background: #fef3c7; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #F59E0B;">
                <p style="margin: 5px 0;"><strong>Numer faktury:</strong> {{ invoice_number }}</p>
                <p style="margin: 5px 0;"><strong>Kwota:</strong> {{ total_amount }}</p>
                <p style="margin: 5px 0;"><strong>Termin płatności:</strong> {{ due_date }}</p>
                <p style="margin: 5px 0;"><strong>Pozostało:</strong> {{ days_until }} dni</p>
            </div>

            <p>Prosimy o terminową płatność.</p>

            <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
                Pozdrawiamy,<br>
                Zespół "Na Piątkę"
            </p>
        </div>
    </div>
</body>
</html>
```

**File**: `templates/emails/overdue_notice.html`

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: #EF4444; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
            <h1 style="margin: 0; font-size: 24px;">Powiadomienie o zaległości</h1>
        </div>

        <div style="background: #fff; padding: 20px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 8px 8px;">
            <p>Dzień dobry,</p>

            <p>Informujemy, że termin płatności faktury {{ invoice_number }} upłynął.</p>

            <div style="background: #fee2e2; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #EF4444;">
                <p style="margin: 5px 0;"><strong>Numer faktury:</strong> {{ invoice_number }}</p>
                <p style="margin: 5px 0;"><strong>Kwota zaległości:</strong> {{ total_amount }}</p>
                <p style="margin: 5px 0;"><strong>Termin płatności był:</strong> {{ due_date }}</p>
                <p style="margin: 5px 0;"><strong>Dni po terminie:</strong> {{ days_overdue }}</p>
            </div>

            <p><strong>Prosimy o niezwłoczną płatność.</strong></p>

            <p>W razie problemów z płatnością, prosimy o kontakt.</p>

            <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
                Pozdrawiamy,<br>
                Zespół "Na Piątkę"
            </p>
        </div>
    </div>
</body>
</html>
```

---

## ADMIN TEMPLATES

**File**: `templates/admin_panel/invoices/dashboard.html`

```html
{% extends "admin_panel/base.html" %}

{% block content %}
<div class="space-y-6">
    <div class="flex items-center justify-between">
        <h1 class="text-2xl font-bold">Panel fakturowania</h1>

        <div x-data="{ month: '' }">
            <div class="flex gap-2">
                <input type="month"
                       class="input input-bordered"
                       x-model="month">
                <button class="btn btn-primary"
                        hx-post="{% url 'invoices:trigger_billing' %}"
                        hx-target="#billing-result"
                        hx-include="[name='month_year']"
                        :disabled="!month">
                    Generuj faktury
                </button>
            </div>
            <input type="hidden" name="month_year" :value="month">
            <div id="billing-result" class="mt-2"></div>
        </div>
    </div>

    <!-- Statistics -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div class="stat bg-base-100 rounded-box shadow">
            <div class="stat-figure text-primary">
                <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                </svg>
            </div>
            <div class="stat-title">Wszystkie faktury</div>
            <div class="stat-value text-primary">{{ total_invoices }}</div>
        </div>

        <div class="stat bg-base-100 rounded-box shadow">
            <div class="stat-figure text-warning">
                <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                          d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
            </div>
            <div class="stat-title">Oczekujące</div>
            <div class="stat-value text-warning">{{ pending_count }}</div>
        </div>

        <div class="stat bg-base-100 rounded-box shadow">
            <div class="stat-figure text-success">
                <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                          d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
            </div>
            <div class="stat-title">Opłacone</div>
            <div class="stat-value text-success">{{ paid_count }}</div>
        </div>

        <div class="stat bg-base-100 rounded-box shadow">
            <div class="stat-figure text-error">
                <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                          d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
                </svg>
            </div>
            <div class="stat-title">Zaległe</div>
            <div class="stat-value text-error">{{ overdue_count }}</div>
        </div>
    </div>

    <!-- Amount Summary -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div class="card bg-warning/10 border border-warning/30">
            <div class="card-body">
                <h3 class="card-title text-warning">Do zapłaty</h3>
                <p class="text-3xl font-bold text-warning">{{ total_outstanding|floatformat:2 }} zł</p>
            </div>
        </div>

        <div class="card bg-success/10 border border-success/30">
            <div class="card-body">
                <h3 class="card-title text-success">Opłacone</h3>
                <p class="text-3xl font-bold text-success">{{ total_paid|floatformat:2 }} zł</p>
            </div>
        </div>
    </div>

    <!-- Recent Invoices -->
    <div class="card bg-base-100 shadow">
        <div class="card-body">
            <h2 class="card-title">Ostatnie faktury</h2>

            <div class="overflow-x-auto">
                <table class="table table-zebra">
                    <thead>
                        <tr>
                            <th>Numer</th>
                            <th>Uczeń</th>
                            <th>Kwota</th>
                            <th>Status</th>
                            <th>Data</th>
                            <th>Akcje</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for invoice in recent_invoices %}
                        <tr>
                            <td>{{ invoice.invoice_number }}</td>
                            <td>{{ invoice.student.get_full_name }}</td>
                            <td>{{ invoice.total_amount|floatformat:2 }} zł</td>
                            <td>
                                {% if invoice.status == 'PAID' %}
                                <span class="badge badge-success">Opłacona</span>
                                {% elif invoice.status == 'OVERDUE' %}
                                <span class="badge badge-error">Zaległa</span>
                                {% else %}
                                <span class="badge">{{ invoice.get_status_display }}</span>
                                {% endif %}
                            </td>
                            <td>{{ invoice.created_at|date:"d.m.Y" }}</td>
                            <td>
                                <a href="{% url 'invoices:detail' invoice.id %}"
                                   class="btn btn-sm btn-ghost">
                                    Zobacz
                                </a>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

**File**: `templates/admin_panel/invoices/partials/_payment_tracker.html`

```html
<div class="space-y-4">
    <!-- Invoice Info -->
    <div class="bg-base-200 rounded-lg p-4">
        <div class="flex items-center justify-between mb-2">
            <span class="text-sm font-medium">Numer faktury:</span>
            <span class="font-mono">{{ invoice.invoice_number }}</span>
        </div>
        <div class="flex items-center justify-between mb-2">
            <span class="text-sm font-medium">Kwota:</span>
            <span class="font-bold text-lg">{{ invoice.total_amount|floatformat:2 }} zł</span>
        </div>
        <div class="flex items-center justify-between mb-2">
            <span class="text-sm font-medium">Termin płatności:</span>
            <span>{{ invoice.due_date|date:"d.m.Y" }}</span>
        </div>
        <div class="flex items-center justify-between">
            <span class="text-sm font-medium">Status:</span>
            {% if invoice.status == 'PAID' %}
            <span class="badge badge-success">Opłacona</span>
            {% elif invoice.status == 'OVERDUE' %}
            <span class="badge badge-error">Zaległa</span>
            {% else %}
            <span class="badge">{{ invoice.get_status_display }}</span>
            {% endif %}
        </div>
    </div>

    {% if invoice.status != 'PAID' %}
    <!-- Mark as Paid Form -->
    <form hx-post="{% url 'invoices:mark_paid' invoice.id %}"
          hx-target="#payment-result"
          hx-swap="innerHTML"
          class="space-y-4">
        {% csrf_token %}

        <div id="payment-result"></div>

        <div class="form-control">
            <label class="label">
                <span class="label-text">Data płatności</span>
            </label>
            <input type="date"
                   name="paid_date"
                   class="input input-bordered w-full"
                   value="{{ 'now'|date:'Y-m-d' }}">
        </div>

        <button type="submit" class="btn btn-success w-full">
            <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                      d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
            Oznacz jako opłacone
        </button>
    </form>

    <div class="divider">lub</div>

    <!-- Create Credit Note -->
    <form hx-post="{% url 'invoices:create_credit_note' invoice.id %}"
          hx-target="#credit-result"
          hx-swap="innerHTML"
          class="space-y-4">
        {% csrf_token %}

        <h3 class="font-semibold">Utwórz notę korygującą</h3>

        <div id="credit-result"></div>

        <div class="form-control">
            <label class="label">
                <span class="label-text">Kwota korekty</span>
            </label>
            <input type="number"
                   step="0.01"
                   name="amount"
                   class="input input-bordered w-full"
                   placeholder="0.00"
                   max="{{ invoice.total_amount }}">
        </div>

        <div class="form-control">
            <label class="label">
                <span class="label-text">Powód korekty</span>
            </label>
            <textarea name="reason"
                      class="textarea textarea-bordered w-full"
                      rows="3"
                      placeholder="Opisz powód korekty..."></textarea>
        </div>

        <button type="submit" class="btn btn-outline w-full">
            Utwórz notę korygującą
        </button>
    </form>
    {% else %}
    <div class="alert alert-success">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
        </svg>
        <span>Faktura została opłacona {{ invoice.paid_date|date:"d.m.Y" }}</span>
    </div>
    {% endif %}
</div>
```

---

## URL CONFIGURATION

**File**: `apps/invoices/urls.py` (rozszerzenie)

```python
from django.urls import path
from . import views

app_name = 'invoices'

urlpatterns = [
    # ... existing urls ...

    # Admin billing
    path('admin/dashboard/', views.AdminBillingDashboardView.as_view(), name='admin_dashboard'),
    path('admin/trigger-billing/', views.TriggerMonthlyBillingView.as_view(), name='trigger_billing'),
    path('admin/<uuid:pk>/payment/', views.PaymentTrackerView.as_view(), name='payment_tracker'),
    path('admin/<uuid:pk>/mark-paid/', views.MarkAsPaidView.as_view(), name='mark_paid'),
    path('admin/<uuid:pk>/credit-note/', views.CreateCreditNoteView.as_view(), name='create_credit_note'),
]
```

---

## COMPLETION CHECKLIST

- [ ] Monthly billing automation working
- [ ] Cron scheduled for 25th of month
- [ ] PDF generation and storage
- [ ] Email delivery with attachments
- [ ] Celery queue processing
- [ ] Payment tracking interface
- [ ] Mark as paid functionality
- [ ] Overdue detection automated
- [ ] Payment reminders (7 days before)
- [ ] Overdue notices (1, 7, 14, 30 days)
- [ ] Credit note generation
- [ ] KOR/YYYY/MM/NNN numbering
- [ ] Billing dashboard statistics
- [ ] No duplicate emails
- [ ] Audit trail complete

---

**Phase 7 Complete**: Full invoicing system operational
**Next Phase**: Phase 8 - Communication System
