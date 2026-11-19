"""Build a consistent demo scenario around a given day.

Keeps users, subjects, rooms and CMS content (run `seed_data --full` first) and
rebuilds everything time-dependent so that, on the demo day:

- every tutor has a regular weekly timetable: 6 weeks of history (completed,
  attendance marked) and 4 weeks ahead (scheduled),
- the tutor jan.kowalski has one past lesson with attendance still to mark,
- the student michal.kowalczyk has an approved cancellation with a makeup
  lesson to book (free slots exist), and can still request another one,
- the admin has a pending cancellation request and a low-attendance alert,
- October invoices exist (paid / overdue / sent), conversations with unread
  messages, notifications, announcements and contact-form leads.

No e-mails are sent and no Celery tasks are queued.

    python manage.py prepare_demo                 # demo tomorrow
    python manage.py prepare_demo --date 2026-11-19
"""

import random
from datetime import date, datetime, time, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

User = get_user_model()

ADMIN = 'admin@napiatke.pl'
JAN, MARIA, TOMASZ, ANNA = (
    'jan.kowalski@napiatke.pl',
    'maria.wisniewska@napiatke.pl',
    'tomasz.nowak@napiatke.pl',
    'anna.lewandowska@napiatke.pl',
)
MICHAL, JULIA, KACPER, ZOFIA, ADAM, NATALIA, JAKUB, MAJA = (
    'michal.kowalczyk@student.pl',
    'julia.zielinska@student.pl',
    'kacper.wojciechowski@student.pl',
    'zofia.kaminska@student.pl',
    'adam.mazur@student.pl',
    'natalia.dabrowska@student.pl',
    'jakub.grabowski@student.pl',
    'maja.pawlak@student.pl',
)
EWA = 'ewa.kowalczyk@rodzic.pl'

# (tutor, students, subject, level, weekday Mon=0, start hour, start minute)
TIMETABLE = [
    (JAN, [MICHAL, ADAM], 'Matematyka', 'Klasa 7-8', 3, 15, 0),
    (JAN, [JULIA], 'Matematyka', 'Matura', 3, 16, 30),
    (JAN, [NATALIA], 'Matematyka', 'Klasa 4-6', 1, 15, 0),
    (JAN, [JULIA], 'Fizyka', 'Matura', 0, 17, 0),
    (MARIA, [KACPER], 'Język Polski', 'Klasa 7-8', 2, 15, 0),
    (MARIA, [MICHAL, ADAM], 'Język Polski', 'Klasa 7-8', 0, 15, 0),
    (MARIA, [JULIA], 'Historia', 'Liceum', 4, 16, 0),
    (TOMASZ, [ZOFIA], 'Język Angielski', 'Liceum', 1, 17, 0),
    (TOMASZ, [MAJA], 'Język Angielski', 'Klasa 4-6', 3, 14, 0),
    (TOMASZ, [MICHAL, ADAM], 'Język Angielski', 'Klasa 7-8', 1, 16, 0),
    (ANNA, [JAKUB], 'Chemia', 'Liceum', 2, 16, 0),
    (ANNA, [JAKUB], 'Biologia', 'Liceum', 4, 15, 0),
    (ANNA, [JULIA], 'Chemia', 'Matura', 3, 18, 0),
]
WEEKS_BACK, WEEKS_AHEAD = 6, 4
HOLIDAYS = {(11, 1), (11, 11), (12, 24), (12, 25), (12, 26)}

# probability of PRESENT / LATE / ABSENT / EXCUSED per student
ATTENDANCE_PROFILE = {
    KACPER: [55, 5, 30, 10],  # triggers the low-attendance alert
    ADAM: [80, 10, 5, 5],
}
DEFAULT_PROFILE = [88, 7, 2, 3]


class Command(BaseCommand):
    help = 'Przygotowuje spójne dane do pokazu aplikacji na wskazany dzień.'

    def add_arguments(self, parser):
        parser.add_argument('--date', help='Dzień pokazu RRRR-MM-DD (domyślnie jutro)')
        parser.add_argument(
            '--force', action='store_true', help='Pozwól uruchomić przy DEBUG=False'
        )

    def handle(self, *args, **opts):
        if not settings.DEBUG and not opts['force']:
            raise CommandError(
                'Ta komenda kasuje zajęcia, faktury i wiadomości. Na produkcji użyj --force.'
            )
        self.day = (
            date.fromisoformat(opts['date'])
            if opts['date']
            else timezone.localdate() + timedelta(days=1)
        )
        self.rng = random.Random(20261119)
        self.u = {u.email: u for u in User.objects.all()}
        missing = [e for e in [ADMIN, JAN, MICHAL, EWA] if e not in self.u]
        if missing:
            raise CommandError(f'Brak kont {missing} — uruchom najpierw: seed_data --full')

        with transaction.atomic():
            self._reset()
            self._lessons()
            self._cancellations()
            self._invoices()
            self._alerts()
            self._conversations()
            self._notifications()
            self._announcements()
            self._leads()
        self._reports()
        self.stdout.write(self.style.SUCCESS(f'Dane demo gotowe na {self.day:%d.%m.%Y}'))

    # ------------------------------------------------------------------ helpers
    def at(self, d, h, m=0):
        return timezone.make_aware(datetime.combine(d, time(h, m)))

    def stamp(self, obj, when, *fields):
        """Override auto_now(_add) timestamps."""
        type(obj).objects.filter(pk=obj.pk).update(**dict.fromkeys(fields, when))

    # -------------------------------------------------------------------- steps
    def _reset(self):
        from apps.attendance.models import AttendanceAlert, AttendanceReport
        from apps.cancellations.models import CancellationRequest, MakeupLesson
        from apps.invoices.models import Invoice
        from apps.landing.models import Lead
        from apps.lessons.models import Lesson
        from apps.messages.models import Conversation
        from apps.notifications.models import Announcement, Notification

        for model in [
            MakeupLesson, CancellationRequest, Invoice, AttendanceAlert,
            AttendanceReport, Lesson, Conversation, Notification, Announcement, Lead,
        ]:
            model.objects.all().delete()

    def _lessons(self):
        from apps.lessons.models import Lesson, LessonStudent
        from apps.rooms.models import Room
        from apps.subjects.models import Level, Subject

        subjects = {s.name: s for s in Subject.objects.all()}
        levels = {lvl.name: lvl for lvl in Level.objects.all()}
        rooms = list(Room.objects.filter(is_active=True).order_by('name'))
        monday = self.day - timedelta(days=self.day.weekday())
        self.lessons = {}  # (tutor, subject, level, date) -> Lesson

        for i, (tutor, studs, subj, lvl, wd, h, m) in enumerate(TIMETABLE):
            subject, room = subjects[subj], rooms[i % len(rooms)]
            group = len(studs) > 1
            for week in range(-WEEKS_BACK, WEEKS_AHEAD + 1):
                d = monday + timedelta(days=7 * week + wd)
                if (d.month, d.day) in HOLIDAYS:
                    continue
                start = self.at(d, h, m)
                past = d < self.day
                lesson = Lesson.objects.create(
                    title=f'{subj} - {"Grupa" if group else self.u[studs[0]].first_name}',
                    subject=subject,
                    level=levels[lvl],
                    tutor=self.u[tutor],
                    room=room,
                    start_time=start,
                    end_time=start + timedelta(minutes=60),
                    is_group_lesson=group,
                    max_participants=4 if group else 1,
                    status='completed' if past else 'scheduled',
                    color=subject.color,
                )
                self.lessons[(tutor, subj, lvl, d)] = lesson
                # Jan's most recent past lesson: attendance left for the live demo
                to_mark = tutor == JAN and past and (self.day - d).days <= 3 and subj == 'Matematyka'
                for email in studs:
                    ls = LessonStudent(lesson=lesson, student=self.u[email])
                    if past and not to_mark:
                        prof = ATTENDANCE_PROFILE.get(email, DEFAULT_PROFILE)
                        ls.attendance_status = self.rng.choices(
                            ['PRESENT', 'LATE', 'ABSENT', 'EXCUSED'], weights=prof
                        )[0]
                        ls.attendance_marked_at = start + timedelta(minutes=5)
                        ls.attendance_marked_by = self.u[tutor]
                    ls.save()

        # Free one-to-one slots with Jan so a makeup lesson can be booked
        self.free_slots = []
        for offset, h, m in [(1, 14, 0), (4, 18, 30), (8, 13, 0)]:
            d = self.day + timedelta(days=offset)
            start = self.at(d, h, m)
            self.free_slots.append(
                Lesson.objects.create(
                    title='Matematyka - wolny termin',
                    subject=subjects['Matematyka'],
                    level=levels['Klasa 7-8'],
                    tutor=self.u[JAN],
                    room=rooms[1 % len(rooms)],
                    start_time=start,
                    end_time=start + timedelta(minutes=60),
                    max_participants=1,
                    status='scheduled',
                    color=subjects['Matematyka'].color,
                    description='Termin do odrabiania zajęć',
                )
            )
        self.stdout.write(f'  zajęcia: {Lesson.objects.count()}')

    def _lesson(self, tutor, subj, lvl, weekday, week):
        monday = self.day - timedelta(days=self.day.weekday())
        return self.lessons[(tutor, subj, lvl, monday + timedelta(days=7 * week + weekday))]

    def _cancellations(self):
        from apps.cancellations.models import CancellationRequest, MakeupLesson
        from apps.lessons.models import LessonStudent

        admin = self.u[ADMIN]

        # Michał: approved two weeks ago -> makeup waiting to be booked
        lesson = self._lesson(JAN, 'Matematyka', 'Klasa 7-8', 3, -2)
        LessonStudent.objects.filter(lesson=lesson, student=self.u[MICHAL]).delete()
        reviewed = lesson.start_time - timedelta(days=1, hours=5)
        req = CancellationRequest.objects.create(
            lesson=lesson,
            student=self.u[MICHAL],
            reason='Wizyta u lekarza',
            status='approved',
            reviewed_by=admin,
            reviewed_at=reviewed,
            admin_notes='Zatwierdzone, proszę wybrać termin odrabiania.',
        )
        self.stamp(req, reviewed - timedelta(hours=20), 'created_at', 'request_date')
        self.makeup = MakeupLesson.objects.create(
            student=self.u[MICHAL],
            original_lesson=lesson,
            expires_at=reviewed + timedelta(days=30),
            notes='Anulowano: Wizyta u lekarza',
        )

        # Julia: pending request -> admin approves it during the demo
        lesson = self._lesson(JAN, 'Fizyka', 'Matura', 0, 1)
        self.pending = CancellationRequest.objects.create(
            lesson=lesson,
            student=self.u[JULIA],
            reason='Wyjazd na olimpiadę fizyczną (etap okręgowy)',
        )
        self.stamp(self.pending, self.at(self.day - timedelta(days=1), 19, 12), 'created_at', 'request_date')

        # Kacper: rejected (less than 24 h before the lesson)
        lesson = self._lesson(MARIA, 'Język Polski', 'Klasa 7-8', 2, -2)
        req = CancellationRequest.objects.create(
            lesson=lesson,
            student=self.u[KACPER],
            reason='Trening piłkarski',
            status='rejected',
            reviewed_by=admin,
            reviewed_at=lesson.start_time - timedelta(hours=6),
            admin_notes='Zgłoszenie mniej niż 24 h przed zajęciami.',
        )
        self.stamp(req, lesson.start_time - timedelta(hours=10), 'created_at', 'request_date')

    def _invoices(self):
        from apps.invoices.models import Invoice
        from apps.invoices.services import invoice_service

        first = self.day.replace(day=1)
        prev = (first - timedelta(days=1)).replace(day=1)
        month_year = prev.strftime('%Y-%m')
        issue = first + timedelta(days=1)
        due = first + timedelta(days=13)
        special = {JAKUB: 'OVERDUE', KACPER: 'OVERDUE', MAJA: 'SENT'}

        for email in [MICHAL, JULIA, KACPER, ZOFIA, ADAM, NATALIA, JAKUB, MAJA]:
            student = self.u[email]
            items = invoice_service.calculate_items_for_month(student, month_year)
            if not items:
                continue
            inv = invoice_service.create_invoice(
                student=student,
                month_year=month_year,
                items=items,
                due_date=due,
                notes=f'Zajęcia za {prev:%m.%Y}',
            )
            status = special.get(email, 'PAID')
            inv.status = status
            inv.issue_date = issue
            if status == 'SENT':
                inv.due_date = self.day + timedelta(days=3)
            if status == 'PAID':
                inv.paid_date = issue + timedelta(days=self.rng.randint(1, 10))
                inv.paid_date = min(inv.paid_date, self.day - timedelta(days=1))
            inv.save()
            self.stamp(inv, self.at(issue, 0, 10), 'created_at')
        self.stdout.write(f'  faktury: {Invoice.objects.count()} ({month_year})')

    def _alerts(self):
        from apps.attendance.models import AttendanceAlert
        from apps.lessons.models import LessonStudent

        qs = LessonStudent.objects.filter(student=self.u[KACPER]).exclude(attendance_status='PENDING')
        total = qs.count() or 1
        present = qs.filter(attendance_status__in=['PRESENT', 'LATE']).count()
        alert = AttendanceAlert.objects.create(
            student=self.u[KACPER],
            attendance_rate=round(present * 100 / total, 1),
            threshold=80,
        )
        self.stamp(alert, self.at(self.day - timedelta(days=1), 7, 0), 'created_at')

    def _conversations(self):
        from apps.messages.models import (
            Conversation,
            ConversationParticipant,
            Message,
            MessageReadReceipt,
        )

        d = self.day
        threads = [
            ('Zadanie domowe - funkcje liniowe', [MICHAL, JAN], [
                (MICHAL, -2, 18, 5, 'Dzień dobry, nie rozumiem zadania 4 z karty pracy. Jak wyznaczyć współczynnik a, jeśli mam dwa punkty?'),
                (JAN, -2, 19, 40, 'Cześć Michał! Liczysz a = (y2 - y1) / (x2 - x1). Podstaw punkty (1, 3) i (3, 7) i daj znać, co wychodzi.'),
                (MICHAL, -2, 20, 2, 'Wychodzi 2, czyli y = 2x + 1. Dziękuję!'),
                (JAN, -1, 16, 15, 'Świetnie. Na czwartek proszę jeszcze zadania 5-7, omówimy je na początku zajęć.'),
            ]),
            ('Postępy Michała przed egzaminem', [EWA, JAN], [
                (EWA, -5, 20, 30, 'Dzień dobry, jak Michał radzi sobie z przygotowaniami do egzaminu ósmoklasisty?'),
                (JAN, -4, 9, 10, 'Dzień dobry! Michał robi wyraźne postępy, szczególnie w geometrii. Warto, żeby w domu rozwiązywał po jednym arkuszu tygodniowo.'),
                (EWA, -4, 21, 0, 'Dziękuję, przypilnuję tego.'),
            ]),
            ('Faktura za zajęcia Jakuba', [EWA, ADMIN], [
                (EWA, -3, 12, 0, 'Dzień dobry, czy mogę zapłacić fakturę za zajęcia Jakuba w dwóch ratach?'),
                (ADMIN, -1, 10, 30, 'Dzień dobry, tak, rozłożymy płatność na dwie raty. Pierwszą proszę opłacić do końca tygodnia.'),
            ]),
            ('Zmiana sali w czwartek', [ADMIN, JAN], [
                (ADMIN, -1, 9, 0, 'Panie Janie, w czwartek o 16:30 Sala 2 jest w remoncie - zajęcia z Julią przenosimy do Sali 3.'),
                (JAN, -1, 9, 45, 'Przyjąłem, dziękuję za informację.'),
            ]),
            ('Materiały do wypracowania', [KACPER, MARIA], [
                (MARIA, -2, 17, 0, 'Kacper, w załączniku do lekcji znajdziesz plan wypracowania. Proszę przynieść szkic na środę.'),
            ]),
        ]
        for subject, people, msgs in threads:
            conv = Conversation.objects.create(subject=subject)
            for email in people:
                ConversationParticipant.objects.create(conversation=conv, user=self.u[email])
            last = None
            for i, (sender, off, h, m, text) in enumerate(msgs):
                when = self.at(d + timedelta(days=off), h, m)
                msg = Message.objects.create(conversation=conv, sender=self.u[sender], content=text)
                self.stamp(msg, when, 'created_at', 'updated_at')
                is_last = i == len(msgs) - 1
                # everything read by everyone except the newest message
                for email in people:
                    if email != sender and not is_last:
                        MessageReadReceipt.objects.create(message=msg, user=self.u[email])
                last = when
            Conversation.objects.filter(pk=conv.pk).update(
                created_at=self.at(d + timedelta(days=msgs[0][1]), msgs[0][2], msgs[0][3]),
                last_message_at=last,
                updated_at=last,
            )

    def _notifications(self):
        from apps.notifications.models import Notification

        d = self.day
        items = [
            (MICHAL, 'REMINDER', 'Przypomnienie o zajęciach', 'Dziś o 15:00 masz zajęcia z matematyki (Jan Kowalski).', 0, 7, False, '/student/calendar/'),
            (MICHAL, 'CANCELLATION', 'Odrabianie do zaplanowania', 'Twoja prośba o anulowanie została zatwierdzona. Wybierz termin odrabiania.', -14, 10, False, '/student/makeup/'),
            (MICHAL, 'MESSAGE', 'Nowa wiadomość od Jan Kowalski', 'Zadanie domowe - funkcje liniowe', -1, 16, False, '/panel/messages/'),
            (MICHAL, 'ATTENDANCE', 'Obecność zapisana', 'Obecność na zajęciach z języka polskiego została zapisana.', -3, 16, True, ''),
            (EWA, 'INVOICE', 'Nowa faktura', 'Wystawiono fakturę za zajęcia z poprzedniego miesiąca.', -17, 8, True, '/parent/invoices/'),
            (EWA, 'INVOICE', 'Faktura po terminie', 'Faktura za zajęcia Jakuba nie została opłacona w terminie.', -4, 8, False, '/parent/invoices/'),
            (EWA, 'MESSAGE', 'Nowa wiadomość od Administrator', 'Faktura za zajęcia Jakuba', -1, 10, False, '/panel/messages/'),
            (JAN, 'ATTENDANCE', 'Uzupełnij obecność', 'Nie zaznaczono obecności na ostatnich zajęciach z matematyki.', 0, 7, False, '/tutor/attendance/'),
            (JAN, 'MESSAGE', 'Nowa wiadomość', 'Zmiana sali w czwartek', -1, 9, True, '/panel/messages/'),
            (ADMIN, 'CANCELLATION', 'Nowa prośba o anulowanie', 'Julia Zielińska prosi o anulowanie zajęć z fizyki.', -1, 19, False, '/panel/cancellations/admin/queue/'),
            (ADMIN, 'ATTENDANCE', 'Niska frekwencja', 'Frekwencja Kacpra Wojciechowskiego spadła poniżej 80%.', -1, 7, False, '/panel/attendance/alerts/'),
            (ADMIN, 'INVOICE', 'Faktury po terminie', '2 faktury za poprzedni miesiąc są nieopłacone.', -4, 8, True, '/panel/invoices/'),
        ]
        for email, typ, title, text, off, h, read, url in items:
            when = self.at(d + timedelta(days=off), h)
            n = Notification.objects.create(
                user=self.u[email], type=typ, title=title, message=text,
                action_url=url, is_read=read, read_at=when if read else None,
                priority='HIGH' if 'termin' in title.lower() or 'frekwencja' in title.lower() else 'NORMAL',
            )
            self.stamp(n, when, 'created_at')

    def _announcements(self):
        from apps.notifications.models import Announcement

        admin = self.u[ADMIN]
        Announcement.objects.create(
            title='Przerwa świąteczna',
            content='W dniach 23.12-1.01 zajęcia się nie odbywają. Zapraszamy ponownie od 2 stycznia!',
            type='INFO', is_pinned=True, created_by=admin,
        )
        Announcement.objects.create(
            title='Próbny egzamin ósmoklasisty',
            content='W sobotę o 10:00 w Sali 1 odbędzie się bezpłatny próbny egzamin z matematyki.',
            type='SUCCESS', target_roles=['student', 'parent'], created_by=admin,
        )
        Announcement.objects.create(
            title='Obecności do końca miesiąca',
            content='Prosimy o uzupełnienie wszystkich obecności przed wystawieniem faktur 25. dnia miesiąca.',
            type='WARNING', target_roles=['tutor'], created_by=admin,
        )

    def _leads(self):
        from apps.landing.models import Lead

        leads = [
            ('Katarzyna Wójcik', 'k.wojcik@example.com', 'Matematyka', 'Szukam korepetycji z matematyki dla córki z 7 klasy, najlepiej we wtorki.', 'new', 0),
            ('Paweł Krawczyk', 'pawel.krawczyk@example.com', 'Język Angielski', 'Czy prowadzą Państwo przygotowanie do FCE w grupie?', 'new', 1),
            ('Monika Szymańska', 'm.szymanska@example.com', 'Chemia', 'Syn przygotowuje się do matury rozszerzonej z chemii.', 'contacted', 4),
            ('Łukasz Jabłoński', 'l.jablonski@example.com', 'Fizyka', 'Pytanie o cenę pakietu 8 zajęć.', 'converted', 12),
        ]
        for name, email, subject, msg, status, days in leads:
            lead = Lead.objects.create(
                name=name, email=email, phone='+48500100200', subject=subject,
                message=msg, status=status, gdpr_consent=True, source='website',
            )
            self.stamp(lead, self.at(self.day - timedelta(days=days + 1), 20, 15), 'created_at')

    def _reports(self):
        """Monthly attendance PDFs for last month (needs WeasyPrint)."""
        try:
            from apps.attendance.services import AttendanceReportService
        except Exception:
            return
        prev = (self.day.replace(day=1) - timedelta(days=1)).replace(day=1)
        service = AttendanceReportService()
        done = 0
        for email in [MICHAL, JULIA, KACPER, ZOFIA, ADAM, NATALIA, JAKUB, MAJA]:
            try:
                service.generate_monthly_report(self.u[email], datetime(prev.year, prev.month, 1))
                done += 1
            except Exception as e:  # pragma: no cover - optional dependency
                self.stdout.write(self.style.WARNING(f'  raport {email}: {e}'))
                break
        self.stdout.write(f'  raporty obecności: {done}')
