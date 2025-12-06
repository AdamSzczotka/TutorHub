from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

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
        if options['with_test_users']:
            self._create_test_users()

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
