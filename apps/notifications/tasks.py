from celery import shared_task


@shared_task
def send_absence_alert_task(student_id: int, lesson_id: int) -> bool:
    """Send absence alert to parent."""
    from apps.accounts.models import User
    from apps.lessons.models import Lesson

    from .services import parent_notification_service

    student = User.objects.get(id=student_id)
    lesson = Lesson.objects.get(id=lesson_id)

    return parent_notification_service.send_absence_alert(student, lesson)


@shared_task
def send_weekly_summaries_task() -> str:
    """Weekly task to send attendance summaries to parents."""
    from .services import parent_notification_service

    sent = parent_notification_service.send_weekly_summaries()
    return f'Sent {sent} weekly summaries'
