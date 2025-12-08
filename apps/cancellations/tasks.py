from celery import shared_task


@shared_task
def send_cancellation_notification_email(request_id, notification_type):
    """Send email notification for cancellation."""
    from django.conf import settings
    from django.core.mail import send_mail
    from django.template.loader import render_to_string

    from .models import CancellationRequest

    request = CancellationRequest.objects.select_related(
        'student', 'lesson', 'lesson__subject'
    ).get(id=request_id)

    if notification_type == 'approved':
        template = 'emails/cancellation_approved.html'
        subject = f'Anulowanie zaakceptowane - {request.lesson.title}'
    else:
        template = 'emails/cancellation_rejected.html'
        subject = f'Anulowanie odrzucone - {request.lesson.title}'

    context = {
        'student_name': request.student.get_full_name(),
        'lesson_title': request.lesson.title,
        'lesson_date': request.lesson.start_time,
        'admin_notes': request.admin_notes,
    }

    html_content = render_to_string(template, context)

    send_mail(
        subject=subject,
        message='',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[request.student.email],
        html_message=html_content,
    )


@shared_task
def notify_admin_new_cancellation(request_id):
    """Notify admins about new cancellation request via email."""
    from django.conf import settings
    from django.core.mail import send_mail
    from django.template.loader import render_to_string

    from apps.accounts.models import User, UserRole

    from .models import CancellationRequest

    request = CancellationRequest.objects.select_related(
        'student', 'lesson', 'lesson__subject'
    ).get(id=request_id)

    admins = User.objects.filter(role=UserRole.ADMIN, is_active=True)

    context = {
        'student_name': request.student.get_full_name(),
        'lesson_title': request.lesson.title,
        'lesson_date': request.lesson.start_time,
        'reason': request.reason,
    }

    html_content = render_to_string('emails/new_cancellation_request.html', context)

    for admin in admins:
        send_mail(
            subject=f'Nowa prosba o anulowanie - {request.lesson.title}',
            message='',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[admin.email],
            html_message=html_content,
        )


@shared_task
def expire_old_makeup_lessons():
    """Periodic task to expire old makeup lessons."""
    from .services import cancellation_service

    expired_count = cancellation_service.expire_old_makeups()
    return f'Expired {expired_count} makeup lessons'


@shared_task
def expire_makeup_lessons():
    """Daily task to expire past deadline makeup lessons with notifications."""
    from .services import expiration_service

    count = expiration_service.expire_past_deadline()
    return f'Expired {count} makeup lessons'


@shared_task
def send_makeup_expiration_warnings():
    """Daily task to send warnings for expiring makeup lessons (7 days before)."""
    from .services import expiration_service

    count = expiration_service.send_expiration_warnings()
    return f'Sent {count} expiration warnings'


# Celery beat schedule example (add to settings.py):
# CELERY_BEAT_SCHEDULE = {
#     'expire-makeup-lessons': {
#         'task': 'apps.cancellations.tasks.expire_makeup_lessons',
#         'schedule': crontab(hour=0, minute=0),  # Every day at midnight
#     },
#     'send-makeup-warnings': {
#         'task': 'apps.cancellations.tasks.send_makeup_expiration_warnings',
#         'schedule': crontab(hour=8, minute=0),  # Every day at 8:00 AM
#     },
# }
