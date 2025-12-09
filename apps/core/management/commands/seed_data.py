"""Seed command for populating the database with test data."""

import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.rooms.models import Room
from apps.subjects.models import Level, Subject, SubjectLevel

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed initial data for the application'

    def add_arguments(self, parser):
        parser.add_argument(
            '--with-test-users',
            action='store_true',
            help='Include test users (development only)',
        )
        parser.add_argument(
            '--full',
            action='store_true',
            help='Create full demo data with lessons and attendance',
        )

    def handle(self, *args, **options):
        self.stdout.write('Seeding data...')

        # Create admin if not exists
        self._create_admin()

        # Create subjects
        self._create_subjects()

        # Create levels
        self._create_levels()

        # Link subjects with levels
        self._create_subject_levels()

        # Create rooms
        self._create_rooms()

        # Create test users if requested
        if options['with_test_users'] or options['full']:
            self._create_test_users()

        # Create full demo data if requested
        if options['full']:
            self._create_full_demo_data()

        self.stdout.write(self.style.SUCCESS('Seeding completed!'))

    def _create_admin(self):
        if not User.objects.filter(email='admin@napiatke.pl').exists():
            User.objects.create_superuser(
                email='admin@napiatke.pl',
                password='admin123',
                first_name='Admin',
                last_name='System',
            )
            self.stdout.write('  Created admin user')

    def _create_subjects(self):
        subjects = [
            {'name': 'Matematyka', 'icon': 'calculator', 'color': '#3B82F6'},
            {'name': 'Język Polski', 'icon': 'book', 'color': '#EF4444'},
            {'name': 'Język Angielski', 'icon': 'globe', 'color': '#10B981'},
            {'name': 'Fizyka', 'icon': 'atom', 'color': '#8B5CF6'},
            {'name': 'Chemia', 'icon': 'flask', 'color': '#F59E0B'},
            {'name': 'Biologia', 'icon': 'leaf', 'color': '#22C55E'},
            {'name': 'Historia', 'icon': 'landmark', 'color': '#6366F1'},
            {'name': 'Geografia', 'icon': 'map', 'color': '#14B8A6'},
        ]
        for data in subjects:
            Subject.objects.get_or_create(name=data['name'], defaults=data)
        self.stdout.write(f'  Created {len(subjects)} subjects')

    def _create_levels(self):
        levels = [
            {'name': 'Klasa 1-3', 'order_index': 1, 'color': '#10B981'},
            {'name': 'Klasa 4-6', 'order_index': 2, 'color': '#3B82F6'},
            {'name': 'Klasa 7-8', 'order_index': 3, 'color': '#8B5CF6'},
            {'name': 'Liceum', 'order_index': 4, 'color': '#EF4444'},
            {'name': 'Matura', 'order_index': 5, 'color': '#F59E0B'},
        ]
        for data in levels:
            Level.objects.get_or_create(name=data['name'], defaults=data)
        self.stdout.write(f'  Created {len(levels)} levels')

    def _create_subject_levels(self):
        subjects = Subject.objects.all()
        levels = Level.objects.all()
        count = 0
        for subject in subjects:
            for level in levels:
                _, created = SubjectLevel.objects.get_or_create(
                    subject=subject,
                    level=level,
                )
                if created:
                    count += 1
        self.stdout.write(f'  Created {count} subject-level links')

    def _create_rooms(self):
        rooms = [
            {
                'name': 'Sala 1',
                'capacity': 6,
                'location': 'Parter',
                'equipment': {'whiteboard': True, 'projector': True},
            },
            {
                'name': 'Sala 2',
                'capacity': 4,
                'location': 'Pierwsze piętro',
                'equipment': {'whiteboard': True, 'computers': True},
            },
            {
                'name': 'Sala 3',
                'capacity': 8,
                'location': 'Parter',
                'equipment': {'whiteboard': True, 'projector': True},
            },
            {
                'name': 'Online',
                'capacity': 20,
                'location': 'Wirtualna',
                'is_virtual': True,
                'equipment': {'video': True, 'screen_share': True},
            },
        ]
        for data in rooms:
            Room.objects.get_or_create(name=data['name'], defaults=data)
        self.stdout.write(f'  Created {len(rooms)} rooms')

    def _create_test_users(self):
        from apps.students.models import StudentProfile
        from apps.tutors.models import TutorProfile

        # Test tutor
        tutor, created = User.objects.get_or_create(
            email='tutor@test.pl',
            defaults={
                'first_name': 'Jan',
                'last_name': 'Kowalski',
                'role': 'tutor',
                'is_profile_completed': True,
                'first_login': False,
            },
        )
        if created:
            tutor.set_password('test123')
            tutor.save()
            TutorProfile.objects.create(
                user=tutor,
                bio='Doświadczony nauczyciel matematyki',
                hourly_rate=45.00,
                experience_years=8,
                is_verified=True,
            )
            self.stdout.write('  Created test tutor')

        # Test student
        student, created = User.objects.get_or_create(
            email='student@test.pl',
            defaults={
                'first_name': 'Anna',
                'last_name': 'Nowak',
                'role': 'student',
                'is_profile_completed': True,
                'first_login': False,
            },
        )
        if created:
            student.set_password('test123')
            student.save()
            StudentProfile.objects.create(
                user=student,
                class_name='7A',
                parent_name='Katarzyna Nowak',
                parent_phone='+48123456789',
                parent_email='rodzic@test.pl',
            )
            self.stdout.write('  Created test student')

    def _create_full_demo_data(self):
        """Create comprehensive demo data for testing all portals."""
        from apps.lessons.models import Lesson, LessonStudent
        from apps.students.models import StudentProfile
        from apps.tutors.models import TutorProfile, TutorSubject

        self.stdout.write('\n  Creating full demo data...')

        # ==================== TUTORS ====================
        tutors_data = [
            {
                'email': 'jan.kowalski@napiatke.pl',
                'first_name': 'Jan',
                'last_name': 'Kowalski',
                'phone': '+48501234567',
                'bio': 'Doświadczony nauczyciel matematyki z 10-letnim stażem. '
                       'Przygotowuję uczniów do matury z matematyki rozszerzonej.',
                'hourly_rate': Decimal('80.00'),
                'experience_years': 10,
                'education': 'Magister matematyki, Uniwersytet Warszawski',
                'subjects': ['Matematyka', 'Fizyka'],
            },
            {
                'email': 'maria.wisniewska@napiatke.pl',
                'first_name': 'Maria',
                'last_name': 'Wiśniewska',
                'phone': '+48502345678',
                'bio': 'Polonistka z pasją. Pomagam w przygotowaniach do egzaminów '
                       'i rozwijam umiejętności pisania.',
                'hourly_rate': Decimal('70.00'),
                'experience_years': 7,
                'education': 'Magister filologii polskiej, Uniwersytet Jagielloński',
                'subjects': ['Język Polski', 'Historia'],
            },
            {
                'email': 'tomasz.nowak@napiatke.pl',
                'first_name': 'Tomasz',
                'last_name': 'Nowak',
                'phone': '+48503456789',
                'bio': 'Native speaker z certyfikatem Cambridge. '
                       'Specjalizuję się w przygotowaniu do egzaminów językowych.',
                'hourly_rate': Decimal('90.00'),
                'experience_years': 5,
                'education': 'Magister filologii angielskiej, Cambridge Certificate',
                'subjects': ['Język Angielski'],
            },
            {
                'email': 'anna.lewandowska@napiatke.pl',
                'first_name': 'Anna',
                'last_name': 'Lewandowska',
                'phone': '+48504567890',
                'bio': 'Chemiczka i biologiczka. Tłumaczę trudne zagadnienia '
                       'w prosty i przystępny sposób.',
                'hourly_rate': Decimal('75.00'),
                'experience_years': 6,
                'education': 'Doktor nauk chemicznych, Politechnika Warszawska',
                'subjects': ['Chemia', 'Biologia'],
            },
        ]

        tutors = []
        subjects = {s.name: s for s in Subject.objects.all()}
        levels = list(Level.objects.all())

        for data in tutors_data:
            tutor, created = User.objects.get_or_create(
                email=data['email'],
                defaults={
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'phone': data['phone'],
                    'role': 'tutor',
                    'is_profile_completed': True,
                    'first_login': False,
                },
            )
            if created:
                tutor.set_password('demo123')
                tutor.save()

                profile = TutorProfile.objects.create(
                    user=tutor,
                    bio=data['bio'],
                    hourly_rate=data['hourly_rate'],
                    experience_years=data['experience_years'],
                    education=data['education'],
                    is_verified=True,
                    verification_date=timezone.now(),
                )

                # Assign subjects to tutor
                for subject_name in data['subjects']:
                    if subject_name in subjects:
                        for level in levels:
                            TutorSubject.objects.get_or_create(
                                tutor=profile,
                                subject=subjects[subject_name],
                                level=level,
                                defaults={
                                    'rate_per_hour': data['hourly_rate'],
                                    'is_active': True,
                                },
                            )

            tutors.append(tutor)

        self.stdout.write(f'    Created {len(tutors_data)} tutors with profiles')

        # ==================== STUDENTS ====================
        students_data = [
            {
                'email': 'michal.kowalczyk@student.pl',
                'first_name': 'Michał',
                'last_name': 'Kowalczyk',
                'class_name': '8A',
                'parent_name': 'Ewa Kowalczyk',
                'parent_phone': '+48601234567',
                'parent_email': 'ewa.kowalczyk@rodzic.pl',
                'learning_goals': 'Przygotowanie do egzaminu ósmoklasisty',
            },
            {
                'email': 'julia.zielinska@student.pl',
                'first_name': 'Julia',
                'last_name': 'Zielińska',
                'class_name': '3LO',
                'parent_name': 'Piotr Zieliński',
                'parent_phone': '+48602345678',
                'parent_email': 'piotr.zielinski@rodzic.pl',
                'learning_goals': 'Matura rozszerzona z matematyki i fizyki',
            },
            {
                'email': 'kacper.wojciechowski@student.pl',
                'first_name': 'Kacper',
                'last_name': 'Wojciechowski',
                'class_name': '7B',
                'parent_name': 'Agnieszka Wojciechowska',
                'parent_phone': '+48603456789',
                'parent_email': 'agnieszka.wojciechowska@rodzic.pl',
                'learning_goals': 'Poprawa ocen z języka polskiego',
            },
            {
                'email': 'zofia.kaminska@student.pl',
                'first_name': 'Zofia',
                'last_name': 'Kamińska',
                'class_name': '2LO',
                'parent_name': 'Robert Kamiński',
                'parent_phone': '+48604567890',
                'parent_email': 'robert.kaminski@rodzic.pl',
                'learning_goals': 'Przygotowanie do certyfikatu FCE',
            },
            {
                'email': 'adam.mazur@student.pl',
                'first_name': 'Adam',
                'last_name': 'Mazur',
                'class_name': '8B',
                'parent_name': 'Magdalena Mazur',
                'parent_phone': '+48605678901',
                'parent_email': 'magdalena.mazur@rodzic.pl',
                'learning_goals': 'Egzamin ósmoklasisty - wszystkie przedmioty',
            },
            {
                'email': 'natalia.dabrowska@student.pl',
                'first_name': 'Natalia',
                'last_name': 'Dąbrowska',
                'class_name': '6A',
                'parent_name': 'Tomasz Dąbrowski',
                'parent_phone': '+48606789012',
                'parent_email': 'tomasz.dabrowski@rodzic.pl',
                'learning_goals': 'Rozwój umiejętności matematycznych',
            },
            {
                'email': 'jakub.grabowski@student.pl',
                'first_name': 'Jakub',
                'last_name': 'Grabowski',
                'class_name': '1LO',
                'parent_name': 'Karolina Grabowska',
                'parent_phone': '+48607890123',
                'parent_email': 'ewa.kowalczyk@rodzic.pl',  # Same parent as Michał (siblings)
                'learning_goals': 'Chemia i biologia na poziomie rozszerzonym',
            },
            {
                'email': 'maja.pawlak@student.pl',
                'first_name': 'Maja',
                'last_name': 'Pawlak',
                'class_name': '5B',
                'parent_name': 'Andrzej Pawlak',
                'parent_phone': '+48608901234',
                'parent_email': 'andrzej.pawlak@rodzic.pl',
                'learning_goals': 'Pomoc w nauce angielskiego',
            },
        ]

        students = []
        for data in students_data:
            student, created = User.objects.get_or_create(
                email=data['email'],
                defaults={
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'role': 'student',
                    'is_profile_completed': True,
                    'first_login': False,
                },
            )
            if created:
                student.set_password('demo123')
                student.save()

                StudentProfile.objects.create(
                    user=student,
                    class_name=data['class_name'],
                    parent_name=data['parent_name'],
                    parent_phone=data['parent_phone'],
                    parent_email=data['parent_email'],
                    learning_goals=data['learning_goals'],
                )

            students.append(student)

        self.stdout.write(f'    Created {len(students_data)} students with profiles')

        # ==================== PARENT ACCOUNTS ====================
        # Create parent accounts with role='parent' and link to children
        from apps.accounts.models import ParentAccess

        # Map parent email to their children (matching parent_email in StudentProfile)
        parents_data = [
            {
                'email': 'ewa.kowalczyk@rodzic.pl',
                'first_name': 'Ewa',
                'last_name': 'Kowalczyk',
                'phone': '+48601234567',
                'children_emails': ['michal.kowalczyk@student.pl', 'jakub.grabowski@student.pl'],
            },
            {
                'email': 'piotr.zielinski@rodzic.pl',
                'first_name': 'Piotr',
                'last_name': 'Zieliński',
                'phone': '+48602345678',
                'children_emails': ['julia.zielinska@student.pl'],
            },
            {
                'email': 'agnieszka.wojciechowska@rodzic.pl',
                'first_name': 'Agnieszka',
                'last_name': 'Wojciechowska',
                'phone': '+48603456789',
                'children_emails': ['kacper.wojciechowski@student.pl'],
            },
            {
                'email': 'robert.kaminski@rodzic.pl',
                'first_name': 'Robert',
                'last_name': 'Kamiński',
                'phone': '+48604567890',
                'children_emails': ['zofia.kaminska@student.pl'],
            },
        ]

        parents = []
        for data in parents_data:
            parent, created = User.objects.get_or_create(
                email=data['email'],
                defaults={
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'phone': data['phone'],
                    'role': 'parent',  # Proper parent role
                    'is_profile_completed': True,
                    'first_login': False,
                },
            )
            if created:
                parent.set_password('demo123')
                parent.save()

                # Create ParentAccess links to children
                for child_email in data.get('children_emails', []):
                    child = User.objects.filter(email=child_email).first()
                    if child:
                        ParentAccess.objects.get_or_create(
                            parent=parent,
                            student=child,
                            defaults={
                                'access_level': 'full',
                                'is_active': True,
                                'can_view_lessons': True,
                                'can_view_attendance': True,
                                'can_view_grades': True,
                                'can_view_invoices': True,
                                'can_message_tutors': True,
                            }
                        )

            parents.append(parent)

        self.stdout.write(f'    Created {len(parents_data)} parent accounts with links to children')

        # ==================== LESSONS ====================
        rooms = list(Room.objects.filter(is_active=True))
        now = timezone.now()

        # Get levels by name for easy access
        levels_dict = {lvl.name: lvl for lvl in levels}

        # Lesson assignments (tutor -> students -> subject -> level)
        lesson_configs = [
            # Jan Kowalski - Matematyka
            {'tutor_idx': 0, 'student_idxs': [0, 4], 'subject': 'Matematyka', 'level': 'Klasa 7-8'},
            {'tutor_idx': 0, 'student_idxs': [1], 'subject': 'Matematyka', 'level': 'Matura'},
            {'tutor_idx': 0, 'student_idxs': [5], 'subject': 'Matematyka', 'level': 'Klasa 4-6'},
            {'tutor_idx': 0, 'student_idxs': [1], 'subject': 'Fizyka', 'level': 'Matura'},
            # Maria Wiśniewska - Polski
            {'tutor_idx': 1, 'student_idxs': [2], 'subject': 'Język Polski', 'level': 'Klasa 7-8'},
            {'tutor_idx': 1, 'student_idxs': [0, 4], 'subject': 'Język Polski', 'level': 'Klasa 7-8'},
            {'tutor_idx': 1, 'student_idxs': [1], 'subject': 'Historia', 'level': 'Liceum'},
            # Tomasz Nowak - Angielski
            {'tutor_idx': 2, 'student_idxs': [3], 'subject': 'Język Angielski', 'level': 'Liceum'},
            {'tutor_idx': 2, 'student_idxs': [7], 'subject': 'Język Angielski', 'level': 'Klasa 4-6'},
            {'tutor_idx': 2, 'student_idxs': [0, 4], 'subject': 'Język Angielski', 'level': 'Klasa 7-8'},
            # Anna Lewandowska - Chemia/Biologia
            {'tutor_idx': 3, 'student_idxs': [6], 'subject': 'Chemia', 'level': 'Liceum'},
            {'tutor_idx': 3, 'student_idxs': [6], 'subject': 'Biologia', 'level': 'Liceum'},
            {'tutor_idx': 3, 'student_idxs': [1], 'subject': 'Chemia', 'level': 'Matura'},
        ]

        lessons_created = 0
        attendance_created = 0

        for config in lesson_configs:
            tutor = tutors[config['tutor_idx']]
            subject = subjects[config['subject']]
            level = levels_dict[config['level']]
            lesson_students = [students[i] for i in config['student_idxs']]
            is_group = len(lesson_students) > 1

            # Create past lessons (completed)
            for days_ago in [28, 21, 14, 7]:
                lesson_time = now - timedelta(days=days_ago)
                # Randomize hour between 14:00 and 18:00
                lesson_time = lesson_time.replace(
                    hour=random.randint(14, 18),
                    minute=random.choice([0, 30]),
                    second=0,
                    microsecond=0,
                )

                lesson = Lesson.objects.create(
                    title=f'{subject.name} - {"Grupa" if is_group else lesson_students[0].first_name}',
                    subject=subject,
                    level=level,
                    tutor=tutor,
                    room=random.choice(rooms),
                    start_time=lesson_time,
                    end_time=lesson_time + timedelta(minutes=60),
                    is_group_lesson=is_group,
                    max_participants=4 if is_group else 1,
                    status='completed',
                    color=subject.color,
                )
                lessons_created += 1

                # Create attendance records
                for student in lesson_students:
                    attendance_status = random.choices(
                        ['PRESENT', 'PRESENT', 'PRESENT', 'LATE', 'ABSENT', 'EXCUSED'],
                        weights=[60, 20, 10, 5, 3, 2],
                    )[0]

                    LessonStudent.objects.create(
                        lesson=lesson,
                        student=student,
                        attendance_status=attendance_status,
                        attendance_marked_at=lesson_time + timedelta(minutes=5),
                        attendance_marked_by=tutor,
                    )
                    attendance_created += 1

            # Create future lessons (scheduled)
            for days_ahead in [0, 7, 14, 21]:
                lesson_time = now + timedelta(days=days_ahead)
                lesson_time = lesson_time.replace(
                    hour=random.randint(14, 18),
                    minute=random.choice([0, 30]),
                    second=0,
                    microsecond=0,
                )

                # Skip if in the past (for today's lessons)
                if lesson_time < now:
                    lesson_time = now + timedelta(hours=2)

                lesson = Lesson.objects.create(
                    title=f'{subject.name} - {"Grupa" if is_group else lesson_students[0].first_name}',
                    subject=subject,
                    level=level,
                    tutor=tutor,
                    room=random.choice(rooms),
                    start_time=lesson_time,
                    end_time=lesson_time + timedelta(minutes=60),
                    is_group_lesson=is_group,
                    max_participants=4 if is_group else 1,
                    status='scheduled',
                    color=subject.color,
                )
                lessons_created += 1

                # Create pending attendance records
                for student in lesson_students:
                    LessonStudent.objects.create(
                        lesson=lesson,
                        student=student,
                        attendance_status='PENDING',
                    )
                    attendance_created += 1

        self.stdout.write(f'    Created {lessons_created} lessons')
        self.stdout.write(f'    Created {attendance_created} attendance records')

        # ==================== SUMMARY ====================
        self.stdout.write('\n  ' + '=' * 50)
        self.stdout.write('  DEMO ACCOUNTS SUMMARY')
        self.stdout.write('  ' + '=' * 50)
        self.stdout.write('  All passwords: demo123')
        self.stdout.write('')
        self.stdout.write('  ADMIN:')
        self.stdout.write('    admin@napiatke.pl (password: admin123)')
        self.stdout.write('')
        self.stdout.write('  TUTORS:')
        for t in tutors_data:
            self.stdout.write(f'    {t["email"]} - {t["first_name"]} {t["last_name"]}')
        self.stdout.write('')
        self.stdout.write('  STUDENTS:')
        for s in students_data:
            self.stdout.write(
                f'    {s["email"]} - {s["first_name"]} {s["last_name"]} ({s["class_name"]})'
            )
        self.stdout.write('')
        self.stdout.write('  PARENTS (can view linked students):')
        for p in parents_data:
            self.stdout.write(f'    {p["email"]} - {p["first_name"]} {p["last_name"]}')
        self.stdout.write('  ' + '=' * 50)
