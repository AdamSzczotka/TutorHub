from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


@shared_task
def monthly_billing_task(month_year=None):
    """Monthly billing automation task.

    Runs on 25th of each month at midnight.
    Generates invoices for next month and sends them.
    """
    from dateutil.relativedelta import relativedelta
    from django.utils import timezone

    from .services import billing_service

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


@shared_task
def generate_single_invoice_task(student_id, month_year):
    """Generate invoice for single student (queued)."""
    from apps.accounts.models import User

    from .services import billing_service

    student = User.objects.get(id=student_id)
    invoice = billing_service._generate_invoice_for_student(student, month_year)

    if invoice:
        logger.info(f"Generated invoice {invoice.invoice_number} for {student.get_full_name()}")
        return {
            'invoice_id': str(invoice.id),
            'invoice_number': invoice.invoice_number
        }
    else:
        logger.info(f"No invoice generated for {student.get_full_name()} - no lessons or already exists")
        return None
