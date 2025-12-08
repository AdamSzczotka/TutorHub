from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

from .models import Notification

User = get_user_model()


class DigestFrequency:
    """Stałe częstotliwości digestów (dla kompatybilności)."""

    HOURLY = 'HOURLY'
    DAILY = 'DAILY'
    WEEKLY = 'WEEKLY'


@shared_task
def send_notification_email(notification_id: str) -> bool:
    """Wysyła email z powiadomieniem."""
    try:
        notification = Notification.objects.select_related('user').get(id=notification_id)
    except Notification.DoesNotExist:
        return False

    user = notification.user
    site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')

    # Renderuj szablon email
    html_content = render_to_string(
        'notifications/email/notification.html',
        {
            'notification': notification,
            'user': user,
            'site_url': site_url,
        },
    )

    # Wyślij email
    try:
        send_mail(
            subject=notification.title,
            message=notification.message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_content,
            fail_silently=False,
        )
        return True
    except Exception:
        return False


@shared_task
def send_hourly_digest() -> str:
    """Wysyła godzinne podsumowanie powiadomień."""
    count = _send_digest(DigestFrequency.HOURLY)
    return f'Sent {count} hourly digests'


@shared_task
def send_daily_digest() -> str:
    """Wysyła dzienne podsumowanie powiadomień."""
    count = _send_digest(DigestFrequency.DAILY)
    return f'Sent {count} daily digests'


@shared_task
def send_weekly_digest() -> str:
    """Wysyła tygodniowe podsumowanie powiadomień."""
    count = _send_digest(DigestFrequency.WEEKLY)
    return f'Sent {count} weekly digests'


def _send_digest(frequency: str) -> int:
    """Wysyła podsumowanie dla określonej częstotliwości.

    Note: NotificationPreference in accounts doesn't have digest_frequency field,
    so we send digests to all active users with email system notifications enabled.
    """
    # Znajdź użytkowników z włączonymi powiadomieniami email
    users = User.objects.filter(
        notification_preferences__email_system=True,
        is_active=True,
    )

    # Określ zakres czasowy
    now = timezone.now()
    if frequency == DigestFrequency.HOURLY:
        start_time = now - timedelta(hours=1)
    elif frequency == DigestFrequency.DAILY:
        start_time = now - timedelta(days=1)
    else:  # WEEKLY
        start_time = now - timedelta(weeks=1)

    site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
    sent_count = 0

    for user in users:
        notifications = Notification.objects.filter(
            user=user,
            created_at__gte=start_time,
            is_read=False,
        ).order_by('-created_at')

        if not notifications.exists():
            continue

        html_content = render_to_string(
            'notifications/email/digest.html',
            {
                'user': user,
                'notifications': notifications,
                'frequency': frequency,
                'site_url': site_url,
            },
        )

        try:
            send_mail(
                subject='Podsumowanie powiadomień - Na Piątkę',
                message=f'Masz {notifications.count()} nieprzeczytanych powiadomień.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_content,
                fail_silently=True,
            )
            sent_count += 1
        except Exception:
            pass

    return sent_count


@shared_task
def cleanup_expired_notifications() -> str:
    """Usuwa wygasłe powiadomienia."""
    now = timezone.now()

    # Usuń wygasłe powiadomienia starsze niż 30 dni
    old_date = now - timedelta(days=30)

    deleted_count, _ = Notification.objects.filter(
        expires_at__lt=now,
        created_at__lt=old_date,
    ).delete()

    # Archiwizuj przeczytane powiadomienia starsze niż 7 dni
    week_ago = now - timedelta(days=7)

    archived_count = Notification.objects.filter(
        is_read=True,
        is_archived=False,
        read_at__lt=week_ago,
    ).update(is_archived=True)

    return f'Deleted {deleted_count}, archived {archived_count}'


@shared_task
def send_absence_alert_task(student_id: int, lesson_id: int) -> bool:
    """Send absence alert to parent."""
    from apps.accounts.models import User
    from apps.lessons.models import Lesson

    from .services import parent_notification_service

    try:
        student = User.objects.get(id=student_id)
        lesson = Lesson.objects.get(id=lesson_id)
        return parent_notification_service.send_absence_alert(student, lesson)
    except (User.DoesNotExist, Lesson.DoesNotExist):
        return False


@shared_task
def send_weekly_summaries_task() -> str:
    """Weekly task to send attendance summaries to parents."""
    from .services import parent_notification_service

    sent = parent_notification_service.send_weekly_summaries()
    return f'Sent {sent} weekly summaries'
