"""Regression tests for access-control and XSS fixes from the security review."""

import json
from datetime import date, timedelta

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import ParentAccess, User
from apps.invoices.models import Invoice
from apps.lessons.models import Lesson, LessonStudent
from apps.messages.services import MessagingService
from apps.subjects.models import Level, Subject
from apps.tutors.models import TutorProfile

PASSWORD = 'Sekretne-haslo-123'


def make_user(email, role, **extra):
    return User.objects.create_user(
        email=email,
        password=PASSWORD,
        first_name=email.split('@')[0],
        last_name='Test',
        role=role,
        first_login=False,
        is_profile_completed=True,
        **extra,
    )


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.clear()


@pytest.fixture
def world(db):
    admin = make_user('admin@t.pl', 'admin')
    tutor_a = make_user('tutor-a@t.pl', 'tutor')
    tutor_b = make_user('tutor-b@t.pl', 'tutor')
    student = make_user('student@t.pl', 'student')
    other_student = make_user('other@t.pl', 'student')
    parent = make_user('parent@t.pl', 'parent')
    ParentAccess.objects.create(parent=parent, student=student, is_active=True)

    subject = Subject.objects.create(name='Matematyka')
    level = Level.objects.create(name='LO')
    start = timezone.now() + timedelta(days=3)
    lesson_b = Lesson.objects.create(
        title='Lekcja B', subject=subject, level=level, tutor=tutor_b,
        start_time=start, end_time=start + timedelta(hours=1),
    )
    LessonStudent.objects.create(lesson=lesson_b, student=other_student)

    today = date.today()
    inv_student = Invoice.objects.create(
        invoice_number='FV/1', student=student, month_year=today.strftime('%Y-%m'),
        issue_date=today, due_date=today,
    )
    inv_other = Invoice.objects.create(
        invoice_number='FV/2', student=other_student, month_year=today.strftime('%Y-%m'),
        issue_date=today, due_date=today,
    )
    return locals()


def login(client, user):
    client.force_login(user)
    return client


# C1 — invoices
@pytest.mark.parametrize('who,visible', [
    ('admin', {'FV/1', 'FV/2'}),
    ('student', {'FV/1'}),
    ('parent', {'FV/1'}),
    ('tutor_a', set()),
])
def test_invoice_list_scoped_by_role(client, world, who, visible):
    login(client, world[who])
    resp = client.get(reverse('invoices:list'))
    assert resp.status_code == 200
    shown = {inv.invoice_number for inv in resp.context['invoices']}
    assert shown == visible


@pytest.mark.parametrize('who', ['tutor_a', 'parent', 'student'])
def test_foreign_invoice_detail_and_pdf_404(client, world, who):
    login(client, world[who])
    pk = world['inv_other'].pk
    assert client.get(reverse('invoices:detail', args=[pk])).status_code == 404
    assert client.get(reverse('invoices:download_pdf', args=[pk])).status_code == 404


def test_parent_invoice_permission_flag(client, world):
    ParentAccess.objects.filter(parent=world['parent']).update(can_view_invoices=False)
    login(client, world['parent'])
    resp = client.get(reverse('invoices:list'))
    assert list(resp.context['invoices']) == []


# H1 — attendance data of other students
@pytest.mark.parametrize('who', ['student', 'parent', 'tutor_a'])
def test_foreign_student_attendance_forbidden(client, world, who):
    login(client, world[who])
    sid = world['other_student'].pk
    for name in ('attendance:history', 'attendance:student_statistics', 'attendance:chart_data'):
        assert client.get(reverse(name, args=[sid])).status_code == 403, name


def test_own_and_child_attendance_allowed(client, world):
    sid = world['student'].pk
    for who in ('student', 'parent', 'admin'):
        login(client, world[who])
        assert client.get(reverse('attendance:student_statistics', args=[sid])).status_code == 200


def test_tutor_sees_own_students_stats(client, world):
    login(client, world['tutor_b'])
    sid = world['other_student'].pk
    assert client.get(reverse('attendance:student_statistics', args=[sid])).status_code == 200


# H2 — marking attendance on someone else's lesson
def test_tutor_cannot_mark_other_tutors_lesson(client, world):
    login(client, world['tutor_a'])
    lesson = world['lesson_b']
    resp = client.post(
        reverse('attendance:mark', args=[lesson.pk]),
        data=json.dumps({'student_id': str(world['other_student'].pk), 'status': 'ABSENT'}),
        content_type='application/json',
    )
    assert resp.status_code == 404
    ls = LessonStudent.objects.get(lesson=lesson)
    assert ls.attendance_status != 'ABSENT'


def test_student_cannot_check_in(client, world):
    login(client, world['other_student'])
    lesson = world['lesson_b']
    resp = client.post(
        reverse('attendance:check_in', args=[lesson.pk, world['other_student'].pk])
    )
    assert resp.status_code == 403


# H3 — tutor cannot change own hourly rate
def test_tutor_cannot_set_hourly_rate(client, world):
    tutor = world['tutor_a']
    TutorProfile.objects.update_or_create(user=tutor, defaults={'hourly_rate': 100})
    login(client, tutor)
    client.post(
        reverse('accounts:profile-step', args=['teaching-info']),
        {'bio': 'Bio', 'hourly_rate': '9999'},
        HTTP_HX_REQUEST='true',
    )
    assert TutorProfile.objects.get(user=tutor).hourly_rate == 100


# M5 — password change requires current password
def test_password_change_requires_old_password(client, world):
    user = world['student']
    login(client, user)
    url = reverse('accounts:profile-step', args=['password-changed'])
    client.post(url, {'new_password': 'Nowe-haslo-456', 'confirm_password': 'Nowe-haslo-456'},
                HTTP_HX_REQUEST='true')
    user.refresh_from_db()
    assert user.check_password(PASSWORD)

    client.post(url, {'old_password': PASSWORD, 'new_password': 'Nowe-haslo-456',
                      'confirm_password': 'Nowe-haslo-456'}, HTTP_HX_REQUEST='true')
    user.refresh_from_db()
    assert user.check_password('Nowe-haslo-456')


# H4 — dangerous attachment types are rejected
def test_html_attachment_rejected(client, world):
    conv, _ = MessagingService.create_conversation(
        creator=world['student'], participant_ids=[world['admin'].id], subject='x',
    )
    login(client, world['student'])
    evil = SimpleUploadedFile('invoice.html', b'<script>alert(1)</script>', content_type='text/html')
    resp = client.post(
        reverse('messages:send', args=[conv.id]),
        {'content': 'hi', 'attachments': [evil]},
    )
    assert resp.status_code == 400


def test_non_participant_cannot_open_conversation(client, world):
    conv, _ = MessagingService.create_conversation(
        creator=world['student'], participant_ids=[world['admin'].id], subject='x',
    )
    login(client, world['other_student'])
    assert client.get(reverse('messages:detail', args=[conv.id])).status_code == 404
    assert client.post(reverse('messages:send', args=[conv.id]), {'content': 'x'}).status_code == 404


# H5 — student name cannot break out of <script> in admin page
def test_student_assignment_json_escaped(client, world):
    s = world['other_student']
    s.first_name = '</script><script>alert(1)</script>'
    s.save()
    login(client, world['admin'])
    resp = client.get(reverse('lessons:students', args=[world['lesson_b'].pk]))
    assert resp.status_code == 200
    body = resp.content.decode()
    assert 'Test' in body  # student list rendered
    assert '</script><script>alert(1)' not in body


# M1 — schedule not leaked to parents/others
def test_parent_calendar_api_only_children(client, world):
    login(client, world['parent'])
    resp = client.get(reverse('lessons:api_events'))
    assert resp.status_code == 200
    assert resp.json() == []


def test_resources_api_admin_only(client, world):
    login(client, world['student'])
    assert client.get(reverse('lessons:api_resources') + '?type=tutors').status_code == 403


# M2 — cannot request cancellation of a lesson you are not enrolled in
def test_student_cannot_cancel_foreign_lesson(world):
    from apps.students.services import StudentCancellationService

    ok, msg = StudentCancellationService.can_cancel_lesson(world['student'], world['lesson_b'])
    assert not ok


# M6 — login is rate limited
def test_login_rate_limited(client, world):
    url = reverse('accounts:login')
    codes = [
        client.post(url, {'username': 'admin@t.pl', 'password': 'wrong'}).status_code
        for _ in range(12)
    ]
    assert codes[-1] == 429


# L2 — parent invitation bound to invited email
def test_invitation_requires_matching_email(client, world):
    access = ParentAccess.objects.create(
        student=world['other_student'], invited_email='invited@t.pl',
        invitation_token='tok123', invitation_sent_at=timezone.now(), is_active=False,
    )
    login(client, world['parent'])  # parent@t.pl, not invited@t.pl
    client.post(reverse('accounts:accept-parent-invitation', args=['tok123']))
    access.refresh_from_db()
    assert access.invitation_accepted_at is None
