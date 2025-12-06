"""Celery tasks for accounts app."""

import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=60,
    retry_backoff_max=600,
    retry_kwargs={'max_retries': 3},
)
def send_welcome_email_task(self, user_id: int, temp_password: str) -> bool:
    """Send welcome email with temporary password.

    Args:
        self: Celery task instance (bound).
        user_id: ID of the user to send email to.
        temp_password: Temporary password to include in email.

    Returns:
        True if email was sent successfully, False otherwise.

    Raises:
        User.DoesNotExist: If user is not found (no retry).
    """
    from apps.accounts.models import User, UserCreationLog

    try:
        user = User.objects.get(id=user_id)

        subject = 'Witamy w Na Piątkę - Twoje dane logowania'

        # Try to render HTML template, fallback to plain text
        try:
            html_message = render_to_string('emails/welcome.html', {
                'user': user,
                'temp_password': temp_password,
                'login_url': f"{getattr(settings, 'SITE_URL', 'http://localhost:8000')}/login/",
            })
        except Exception:
            html_message = None

        # Plain text message
        plain_message = f"""
Witaj {user.first_name}!

Twoje konto w systemie Na Piątkę zostało utworzone.

Dane logowania:
Email: {user.email}
Hasło tymczasowe: {temp_password}

Po pierwszym zalogowaniu zostaniesz poproszony/a o zmianę hasła.

Pozdrawiamy,
Zespół Na Piątkę
"""

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@napiatke.pl'),
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

        # Update creation log
        UserCreationLog.objects.filter(
            created_user=user
        ).update(
            email_sent=True,
            email_sent_at=timezone.now(),
        )

        return True
    except User.DoesNotExist:
        # Don't retry for non-existent users
        logger.warning('Failed to send welcome email: User %s does not exist', user_id)
        return False


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=60,
    retry_backoff_max=600,
    retry_kwargs={'max_retries': 3},
)
def send_password_reset_email_task(self, user_id: int, temp_password: str) -> bool:
    """Send password reset email with new temporary password.

    Args:
        self: Celery task instance (bound).
        user_id: ID of the user to send email to.
        temp_password: New temporary password.

    Returns:
        True if email was sent successfully, False otherwise.

    Raises:
        User.DoesNotExist: If user is not found (no retry).
    """
    from apps.accounts.models import User

    try:
        user = User.objects.get(id=user_id)

        subject = 'Na Piątkę - Reset hasła'

        plain_message = f"""
Witaj {user.first_name}!

Twoje hasło zostało zresetowane przez administratora.

Nowe hasło tymczasowe: {temp_password}

Po zalogowaniu zostaniesz poproszony/a o zmianę hasła.

Pozdrawiamy,
Zespół Na Piątkę
"""

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@napiatke.pl'),
            recipient_list=[user.email],
            fail_silently=False,
        )

        return True
    except User.DoesNotExist:
        # Don't retry for non-existent users
        logger.warning('Failed to send password reset email: User %s does not exist', user_id)
        return False
