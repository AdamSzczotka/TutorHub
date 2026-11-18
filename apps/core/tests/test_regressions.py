"""Regression tests for functional bugs found during the bug hunt."""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.invoices.models import Invoice, InvoiceStatus
from apps.lessons.models import Lesson, LessonStudent
from apps.subjects.models import Level, Subject


def make_user(email, role):
    return User.objects.create_user(
        email=email, password='x-Pass-123', first_name=email.split('@')[0],
        last_name='T', role=role, first_login=False, is_profile_completed=True,
    )


def test_beat_schedule_contains_all_jobs():
    """celery.py used to overwrite CELERY_BEAT_SCHEDULE, and base.__all__ hid it."""
    from napiatke.celery import app

    tasks = {e['task'] for e in app.conf.beat_schedule.values()}
    assert {
        'apps.invoices.tasks.monthly_billing_task',
        'apps.invoices.tasks.check_overdue_invoices_task',
        'apps.cancellations.tasks.expire_makeup_lessons',
        'apps.lessons.tasks.send_lesson_reminders',
    } <= tasks


def test_login_redirect_settings_loaded():
    assert settings.LOGIN_REDIRECT_URL == 'accounts:login-redirect'


@pytest.mark.django_db
def test_approving_cancellation_keeps_group_lesson_for_others():
    from apps.cancellations.models import CancellationRequest
    from apps.cancellations.services import cancellation_service

    admin = make_user('a@t.pl', 'admin')
    tutor = make_user('t@t.pl', 'tutor')
    s1, s2 = make_user('s1@t.pl', 'student'), make_user('s2@t.pl', 'student')
    start = timezone.now() + timedelta(days=5)
    lesson = Lesson.objects.create(
        title='Grupa', subject=Subject.objects.create(name='M'), level=Level.objects.create(name='L'),
        tutor=tutor, start_time=start, end_time=start + timedelta(hours=1),
    )
    LessonStudent.objects.create(lesson=lesson, student=s1)
    LessonStudent.objects.create(lesson=lesson, student=s2)
    req = CancellationRequest.objects.create(lesson=lesson, student=s1, reason='Wyjazd rodzinny')

    cancellation_service.approve_request(req, admin)

    lesson.refresh_from_db()
    assert lesson.status == 'scheduled'
    assert list(lesson.lesson_students.values_list('student', flat=True)) == [s2.id]


@pytest.mark.django_db
def test_invoice_pdf_generates():
    from apps.invoices.pdf_service import pdf_service

    student = make_user('s@t.pl', 'student')
    inv = Invoice.objects.create(
        invoice_number='FV/2026/12/001', student=student, month_year='2026-12',
        issue_date=date.today(), due_date=date.today(),
    )
    pdf = pdf_service.generate_pdf(inv).getvalue()
    assert pdf.startswith(b'%PDF')


@pytest.mark.django_db
def test_admin_dashboard_stats_are_computed(client):
    admin = make_user('a@t.pl', 'admin')
    student = make_user('s@t.pl', 'student')
    today = timezone.localdate()
    Invoice.objects.create(invoice_number='1', student=student, month_year='x', issue_date=today,
                           due_date=today, status=InvoiceStatus.SENT)
    Invoice.objects.create(invoice_number='2', student=student, month_year='y', issue_date=today,
                           due_date=today, status=InvoiceStatus.PAID, paid_date=today,
                           total_amount=Decimal('123.00'))
    client.force_login(admin)
    stats = client.get(reverse('admin_panel:dashboard')).context['stats']
    assert stats['pending_invoices'] == 1
    assert stats['monthly_revenue'] == Decimal('123.00')
