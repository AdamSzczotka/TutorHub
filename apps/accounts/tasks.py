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


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=60,
    retry_backoff_max=600,
    retry_kwargs={'max_retries': 3},
)
def send_verification_email_task(self, verification_id: int) -> bool:
    """Send email verification link.

    Args:
        self: Celery task instance (bound).
        verification_id: ID of the UserVerification to send.

    Returns:
        True if email was sent successfully, False otherwise.
    """
    from apps.accounts.models import UserVerification

    try:
        verification = UserVerification.objects.select_related('user').get(id=verification_id)
        user = verification.user

        subject = 'Na Piątkę - Weryfikacja adresu email'

        verification_url = (
            f"{getattr(settings, 'SITE_URL', 'http://localhost:8000')}"
            f"/accounts/verify/{verification.token}/"
        )

        plain_message = f"""
Witaj {user.first_name}!

Kliknij poniższy link, aby zweryfikować swój adres email:

{verification_url}

Link jest ważny przez 24 godziny.

Pozdrawiamy,
Zespół Na Piątkę
"""

        try:
            html_message = render_to_string('emails/verification.html', {
                'user': user,
                'verification_url': verification_url,
            })
        except Exception:
            html_message = None

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@napiatke.pl'),
            recipient_list=[verification.value_to_verify],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info('Verification email sent to %s', verification.value_to_verify)
        return True

    except UserVerification.DoesNotExist:
        logger.warning('Verification %s does not exist', verification_id)
        return False


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=60,
    retry_backoff_max=600,
    retry_kwargs={'max_retries': 3},
)
def send_parent_invitation_email_task(self, access_id: int) -> bool:
    """Send parent portal invitation email.

    Args:
        self: Celery task instance (bound).
        access_id: ID of the ParentAccess invitation.

    Returns:
        True if email was sent successfully, False otherwise.
    """
    from apps.accounts.models import ParentAccess

    try:
        access = ParentAccess.objects.select_related('student').get(id=access_id)

        subject = 'Na Piątkę - Zaproszenie do portalu rodzica'

        invitation_url = (
            f"{getattr(settings, 'SITE_URL', 'http://localhost:8000')}"
            f"/accounts/parent-invitation/{access.invitation_token}/"
        )

        student_name = access.student.get_full_name()

        plain_message = f"""
Witaj!

Zostałeś/aś zaproszony/a do portalu rodzica w systemie Na Piątkę.

Uczeń: {student_name}

Kliknij poniższy link, aby zaakceptować zaproszenie i uzyskać dostęp:

{invitation_url}

Dzięki temu będziesz mógł/mogła:
- Przeglądać harmonogram lekcji
- Sprawdzać obecności
- Kontaktować się z korepetytorami

Pozdrawiamy,
Zespół Na Piątkę
"""

        try:
            html_message = render_to_string('emails/parent_invitation.html', {
                'student_name': student_name,
                'invitation_url': invitation_url,
                'access': access,
            })
        except Exception:
            html_message = None

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@napiatke.pl'),
            recipient_list=[access.invited_email],
            html_message=html_message,
            fail_silently=False,
        )

        # Update sent timestamp
        access.invitation_sent_at = timezone.now()
        access.save(update_fields=['invitation_sent_at'])

        logger.info('Parent invitation sent to %s for student %s', access.invited_email, student_name)
        return True

    except ParentAccess.DoesNotExist:
        logger.warning('ParentAccess %s does not exist', access_id)
        return False
