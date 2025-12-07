from datetime import timedelta

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

from celery import shared_task

from .models import Lesson


@shared_task
def send_lesson_reminders():
    """Send reminder emails 24h before lessons."""
    tomorrow = timezone.now() + timedelta(days=1)
    tomorrow_start = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow_end = tomorrow.replace(hour=23, minute=59, second=59, microsecond=999999)

    lessons = (
        Lesson.objects.filter(
            start_time__gte=tomorrow_start,
            start_time__lte=tomorrow_end,
            status='scheduled',
        )
        .select_related('subject', 'level', 'tutor', 'room')
        .prefetch_related('lesson_students__student')
    )

    for lesson in lessons:
        # Send to tutor
        send_lesson_reminder_email.delay(
            lesson_id=lesson.id,
            recipient_id=lesson.tutor_id,
            recipient_type='tutor',
        )

        # Send to students
        for ls in lesson.lesson_students.all():
            send_lesson_reminder_email.delay(
                lesson_id=lesson.id,
                recipient_id=ls.student_id,
                recipient_type='student',
            )


@shared_task
def send_lesson_reminder_email(
    lesson_id: int,
    recipient_id: int,
    recipient_type: str,
):
    """Send individual reminder email."""
    from apps.accounts.models import User

    lesson = Lesson.objects.select_related('subject', 'level', 'tutor', 'room').get(
        pk=lesson_id
    )

    recipient = User.objects.get(pk=recipient_id)

    context = {
        'lesson': lesson,
        'recipient': recipient,
        'recipient_type': recipient_type,
    }

    subject = f'Przypomnienie: Zajecia jutro - {lesson.title}'
    html_message = render_to_string('emails/lesson_reminder.html', context)
    plain_message = render_to_string('emails/lesson_reminder.txt', context)

    send_mail(
        subject=subject,
        message=plain_message,
        html_message=html_message,
        from_email=None,
        recipient_list=[recipient.email],
        fail_silently=False,
    )


@shared_task
def send_lesson_created_notification(lesson_id: int):
    """Notify participants about new lesson."""
    lesson = (
        Lesson.objects.select_related('subject', 'level', 'tutor', 'room')
        .prefetch_related('lesson_students__student')
        .get(pk=lesson_id)
    )

    recipients = [lesson.tutor.email]
    for ls in lesson.lesson_students.all():
        recipients.append(ls.student.email)

    context = {'lesson': lesson}
    subject = f'Nowe zajecia: {lesson.title}'
    html_message = render_to_string('emails/lesson_created.html', context)

    for email in recipients:
        send_mail(
            subject=subject,
            message='',
            html_message=html_message,
            from_email=None,
            recipient_list=[email],
            fail_silently=True,
        )


@shared_task
def send_lesson_cancelled_notification(lesson_id: int, reason: str = ''):
    """Notify participants about cancelled lesson."""
    lesson = (
        Lesson.objects.select_related('subject', 'level', 'tutor', 'room')
        .prefetch_related('lesson_students__student')
        .get(pk=lesson_id)
    )

    recipients = [lesson.tutor.email]
    for ls in lesson.lesson_students.all():
        recipients.append(ls.student.email)

    context = {'lesson': lesson, 'reason': reason}
    subject = f'Odwolane zajecia: {lesson.title}'
    html_message = render_to_string('emails/lesson_cancelled.html', context)

    for email in recipients:
        send_mail(
            subject=subject,
            message='',
            html_message=html_message,
            from_email=None,
            recipient_list=[email],
            fail_silently=True,
        )


@shared_task
def send_lesson_updated_notification(lesson_id: int, changes: dict | None = None):
    """Notify participants about lesson changes."""
    lesson = (
        Lesson.objects.select_related('subject', 'level', 'tutor', 'room')
        .prefetch_related('lesson_students__student')
        .get(pk=lesson_id)
    )

    recipients = [lesson.tutor.email]
    for ls in lesson.lesson_students.all():
        recipients.append(ls.student.email)

    context = {'lesson': lesson, 'changes': changes or {}}
    subject = f'Zmiana w zajeciach: {lesson.title}'
    html_message = render_to_string('emails/lesson_updated.html', context)

    for email in recipients:
        send_mail(
            subject=subject,
            message='',
            html_message=html_message,
            from_email=None,
            recipient_list=[email],
            fail_silently=True,
        )
