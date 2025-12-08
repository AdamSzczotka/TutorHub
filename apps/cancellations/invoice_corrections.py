"""
Invoice correction service stub for cancellations.

This module will be fully implemented when the invoices app is created in Phase 7.
For now, it provides placeholder methods that can be called without errors.
"""

from django.db import transaction


class InvoiceCorrectionService:
    """Service for invoice corrections after cancellations."""

    @transaction.atomic
    def correct_for_cancellation(self, lesson, student):
        """Remove cancelled lesson from invoice.

        This is a stub that will be implemented when invoices app exists.
        """
        # TODO: Implement when invoices app is created in Phase 7
        # from apps.invoices.models import InvoiceItem, Invoice

        # invoice_item = InvoiceItem.objects.filter(
        #     lesson=lesson,
        #     invoice__student=student,
        #     invoice__status__in=['GENERATED', 'SENT']
        # ).select_related('invoice').first()

        # if not invoice_item:
        #     return None  # Not billed yet

        # ... correction logic
        return None

    @transaction.atomic
    def create_credit_note(self, original_invoice, lesson, amount):
        """Create credit note for already paid invoice.

        This is a stub that will be implemented when invoices app exists.
        """
        # TODO: Implement when invoices app is created in Phase 7
        return None


invoice_correction_service = InvoiceCorrectionService()
