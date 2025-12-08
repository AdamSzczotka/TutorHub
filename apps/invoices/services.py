from datetime import datetime
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from django.db import transaction
from django.utils import timezone

from .models import Invoice, InvoiceItem, InvoiceStatus
from .utils import VAT_STANDARD, round_currency


class InvoiceService:
    """Service for invoice management."""

    VAT_RATE = VAT_STANDARD

    def calculate_item_total(self, quantity, unit_price) -> dict:
        """Calculate line item total.

        Args:
            quantity: Number of units.
            unit_price: Price per unit.

        Returns:
            Dict with quantity, unit_price, total_price.
        """
        total = Decimal(str(quantity)) * Decimal(str(unit_price))
        return {
            'quantity': round_currency(quantity),
            'unit_price': round_currency(unit_price),
            'total_price': round_currency(total),
        }

    def calculate_invoice_totals(self, items: list) -> dict:
        """Calculate invoice totals with VAT.

        Args:
            items: List of items with total_price.

        Returns:
            Dict with net_amount, vat_amount, total_amount.
        """
        net_amount = sum(item['total_price'] for item in items)
        vat_amount = net_amount * self.VAT_RATE
        total_amount = net_amount + vat_amount

        return {
            'net_amount': round_currency(net_amount),
            'vat_amount': round_currency(vat_amount),
            'total_amount': round_currency(total_amount),
        }

    def calculate_items_for_month(self, student, month_year: str) -> list:
        """Calculate invoice items for student's monthly lessons.

        Args:
            student: Student user.
            month_year: Month in YYYY-MM format.

        Returns:
            List of item dicts with lesson, description, quantity, etc.
        """
        from apps.lessons.models import Lesson

        year, month = map(int, month_year.split('-'))
        start_date = datetime(year, month, 1, tzinfo=timezone.get_current_timezone())
        end_date = start_date + relativedelta(months=1)

        # Get completed/scheduled lessons for the month
        lessons = Lesson.objects.filter(
            lesson_students__student=student,
            start_time__gte=start_date,
            start_time__lt=end_date,
            status__in=['scheduled', 'completed'],
        ).select_related('subject', 'tutor', 'tutor__tutor_profile')

        items = []
        for lesson in lessons:
            # Get hourly rate from tutor profile or default
            tutor_profile = getattr(lesson.tutor, 'tutor_profile', None)
            hourly_rate = (
                tutor_profile.hourly_rate
                if tutor_profile and tutor_profile.hourly_rate
                else Decimal('100.00')
            )

            # Calculate duration in hours
            duration = (lesson.end_time - lesson.start_time).total_seconds() / 3600
            duration = Decimal(str(duration))

            item_calc = self.calculate_item_total(duration, hourly_rate)

            items.append({
                'lesson': lesson,
                'description': (
                    f"{lesson.subject.name} ({lesson.start_time.strftime('%d.%m.%Y')})"
                ),
                **item_calc,
            })

        return items

    def generate_invoice_number(self, month_year: str) -> str:
        """Generate sequential invoice number (FV/YYYY/MM/NNN).

        Args:
            month_year: Month in YYYY-MM format.

        Returns:
            Invoice number string.
        """
        year, month = month_year.split('-')

        # Find last invoice for this month
        prefix = f"FV/{year}/{month}/"
        last_invoice = (
            Invoice.objects.filter(invoice_number__startswith=prefix)
            .order_by('-invoice_number')
            .first()
        )

        if last_invoice:
            last_num = int(last_invoice.invoice_number.split('/')[-1])
            sequence = last_num + 1
        else:
            sequence = 1

        return f"{prefix}{str(sequence).zfill(3)}"

    @transaction.atomic
    def create_invoice(
        self,
        student,
        month_year: str,
        items: list,
        due_date,
        notes: str = '',
    ) -> Invoice:
        """Create invoice for student.

        Args:
            student: Student user.
            month_year: Month in YYYY-MM format.
            items: List of item dicts.
            due_date: Payment due date.
            notes: Optional notes.

        Returns:
            Created Invoice instance.
        """
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
            notes=notes,
        )

        # Create invoice items
        for i, item in enumerate(items):
            InvoiceItem.objects.create(
                invoice=invoice,
                lesson=item.get('lesson'),
                description=item['description'],
                quantity=item_calculations[i]['quantity'],
                unit_price=item_calculations[i]['unit_price'],
                total_price=item_calculations[i]['total_price'],
            )

        return invoice

    def update_status(
        self,
        invoice_id,
        status: str,
        paid_date=None,
        notes: str = None,
    ) -> Invoice:
        """Update invoice status.

        Args:
            invoice_id: Invoice UUID.
            status: New status.
            paid_date: Date of payment (for PAID status).
            notes: Optional notes to add.

        Returns:
            Updated Invoice instance.
        """
        invoice = Invoice.objects.get(id=invoice_id)
        invoice.status = status

        if paid_date:
            invoice.paid_date = paid_date
        if notes:
            invoice.notes = notes

        invoice.save()
        return invoice

    def get_by_id(self, invoice_id):
        """Get invoice with all relations.

        Args:
            invoice_id: Invoice UUID.

        Returns:
            Invoice instance with related data.
        """
        return (
            Invoice.objects.select_related('student', 'student__student_profile')
            .prefetch_related('items', 'items__lesson', 'items__lesson__subject')
            .get(id=invoice_id)
        )

    def get_student_invoices(self, student, status: str = None):
        """Get all invoices for student.

        Args:
            student: Student user.
            status: Optional status filter.

        Returns:
            QuerySet of invoices.
        """
        queryset = Invoice.objects.filter(student=student)
        if status:
            queryset = queryset.filter(status=status)
        return queryset.order_by('-issue_date')


invoice_service = InvoiceService()


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
            role='student',
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
        due_date = datetime(year, month, 14, tzinfo=timezone.get_current_timezone()).date()

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
        from .pdf_service import pdf_service

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

        from django.conf import settings
        from django.core.mail import EmailMessage
        from django.template.loader import render_to_string

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
                if pdf_path.exists():
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
        if profile and hasattr(profile, 'parent_email') and profile.parent_email:
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
        from datetime import timedelta

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
        from datetime import timedelta

        from django.conf import settings
        from django.core.mail import send_mail
        from django.template.loader import render_to_string

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
        from django.conf import settings
        from django.core.mail import send_mail
        from django.template.loader import render_to_string

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


class CorrectionService:
    """Service for invoice corrections."""

    @transaction.atomic
    def create_credit_note(self, original_invoice, amount, reason):
        """Create credit note for invoice."""
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
