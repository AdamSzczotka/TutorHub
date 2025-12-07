"""Celery tasks for landing app."""

import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=60,
    retry_backoff_max=600,
    retry_kwargs={'max_retries': 3},
)
def notify_new_lead(self, lead_id: int) -> bool:
    """Send notification about new lead/contact form submission.

    Args:
        self: Celery task instance (bound).
        lead_id: ID of the Lead to notify about.

    Returns:
        True if notification was sent successfully, False otherwise.
    """
    from apps.landing.models import Lead

    try:
        lead = Lead.objects.get(id=lead_id)

        subject = f'[Na Piątkę] Nowa wiadomość od: {lead.name}'

        message = f"""
Nowa wiadomość z formularza kontaktowego:

Imię: {lead.name}
Email: {lead.email}
Telefon: {lead.phone or "Nie podano"}
Temat: {lead.subject}

Wiadomość:
{lead.message}

---
Zgoda RODO: {"Tak" if lead.gdpr_consent else "Nie"}
Zgoda marketingowa: {"Tak" if lead.marketing_consent else "Nie"}
Data: {lead.created_at.strftime('%Y-%m-%d %H:%M')}
"""

        admin_email = getattr(settings, 'ADMIN_EMAIL', None)
        if not admin_email:
            admin_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'admin@napiatke.pl')

        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@napiatke.pl'),
            recipient_list=[admin_email],
            fail_silently=False,
        )

        logger.info('Lead notification sent for lead %s', lead_id)
        return True

    except Lead.DoesNotExist:
        logger.warning('Lead %s does not exist', lead_id)
        return False
