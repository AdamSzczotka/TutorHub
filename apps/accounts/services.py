"""Services for accounts app."""

import csv
import hashlib
import io
import json
import logging
import re
from dataclasses import dataclass
from datetime import timedelta
from typing import Dict, List, Optional, Tuple

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.utils import timezone

User = get_user_model()
logger = logging.getLogger(__name__)

# Maximum rows allowed for CSV import to prevent DoS
MAX_CSV_IMPORT_ROWS = 1000


@dataclass
class ProfileStep:
    """Represents a profile completion step."""

    id: str
    title: str
    required_fields: List[str]
    is_complete: bool


class ProfileCompletionService:
    """Service for calculating profile completion."""

    def __init__(self, user: User):
        self.user = user
        self.steps = self._get_steps()

    def _get_steps(self) -> List[ProfileStep]:
        """Get profile completion steps based on user role."""
        base_steps = [
            ProfileStep(
                id='basic-info',
                title='Podstawowe informacje',
                required_fields=['first_name', 'last_name', 'phone'],
                is_complete=bool(
                    self.user.first_name and self.user.last_name and self.user.phone
                ),
            ),
            ProfileStep(
                id='password-changed',
                title='Zmiana hasła',
                required_fields=['password'],
                is_complete=not self.user.first_login,
            ),
        ]

        if self.user.is_student:
            profile = getattr(self.user, 'student_profile', None)
            base_steps.extend([
                ProfileStep(
                    id='parent-info',
                    title='Dane rodzica/opiekuna',
                    required_fields=['parent_name', 'parent_email', 'parent_phone'],
                    is_complete=bool(
                        profile
                        and profile.parent_name
                        and profile.parent_email
                        and profile.parent_phone
                    ),
                ),
                ProfileStep(
                    id='academic-info',
                    title='Informacje szkolne',
                    required_fields=['class_name', 'learning_goals'],
                    is_complete=bool(
                        profile and profile.class_name and profile.learning_goals
                    ),
                ),
            ])

        elif self.user.is_tutor:
            profile = getattr(self.user, 'tutor_profile', None)
            base_steps.extend([
                ProfileStep(
                    id='professional-info',
                    title='Informacje zawodowe',
                    required_fields=['education', 'experience_years'],
                    is_complete=bool(
                        profile
                        and profile.education
                        and profile.experience_years is not None
                    ),
                ),
                ProfileStep(
                    id='teaching-info',
                    title='Informacje o nauczaniu',
                    required_fields=['bio', 'hourly_rate'],
                    is_complete=bool(profile and profile.bio and profile.hourly_rate),
                ),
            ])

        return base_steps

    @property
    def percentage(self) -> int:
        """Calculate completion percentage."""
        if not self.steps:
            return 100
        completed = sum(1 for step in self.steps if step.is_complete)
        return int((completed / len(self.steps)) * 100)

    @property
    def completed_steps(self) -> int:
        """Count completed steps."""
        return sum(1 for step in self.steps if step.is_complete)

    @property
    def total_steps(self) -> int:
        """Count total steps."""
        return len(self.steps)

    @property
    def next_step(self) -> Optional[ProfileStep]:
        """Get next incomplete step."""
        for step in self.steps:
            if not step.is_complete:
                return step
        return None

    @property
    def missing_fields(self) -> List[str]:
        """Get all missing required fields."""
        fields = []
        for step in self.steps:
            if not step.is_complete:
                fields.extend(step.required_fields)
        return fields

    def get_step_by_id(self, step_id: str) -> Optional[ProfileStep]:
        """Get step by ID."""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None


class UserImportService:
    """Service for importing users from CSV."""

    REQUIRED_COLUMNS = ['email', 'first_name', 'last_name', 'role']
    OPTIONAL_COLUMNS = [
        'phone',
        'class_name',
        'parent_name',
        'parent_email',
        'parent_phone',
    ]

    def __init__(self, csv_content: str, created_by: User):
        self.csv_content = csv_content
        self.created_by = created_by
        self.errors: List[Dict] = []
        self.valid_rows: List[Dict] = []

    def validate(self) -> Tuple[int, int, List[Dict]]:
        """Validate CSV and return (total, valid, errors)."""
        try:
            reader = csv.DictReader(io.StringIO(self.csv_content))

            # Check columns
            missing_cols = set(self.REQUIRED_COLUMNS) - set(reader.fieldnames or [])
            if missing_cols:
                self.errors.append({
                    'row': 0,
                    'errors': [f'Brakujące kolumny: {", ".join(missing_cols)}'],
                })
                return 0, 0, self.errors

            row_count = 0
            for idx, row in enumerate(reader, start=2):
                row_count += 1

                # Check row limit to prevent DoS
                if row_count > MAX_CSV_IMPORT_ROWS:
                    self.errors.append({
                        'row': idx,
                        'errors': [
                            f'Przekroczono limit {MAX_CSV_IMPORT_ROWS} wierszy. '
                            'Podziel plik na mniejsze części.'
                        ],
                    })
                    break

                row_errors = self._validate_row(row, idx)
                if row_errors:
                    self.errors.append({
                        'row': idx,
                        'errors': row_errors,
                    })
                else:
                    self.valid_rows.append(row)

            return (
                len(self.valid_rows) + len(self.errors),
                len(self.valid_rows),
                self.errors,
            )

        except Exception as e:
            logger.exception('Error parsing CSV')
            self.errors.append({'row': 0, 'errors': [f'Błąd parsowania CSV: {str(e)}']})
            return 0, 0, self.errors

    def _validate_row(self, row: Dict, idx: int) -> List[str]:
        """Validate single row."""
        errors = []

        # Required fields
        if not row.get('email'):
            errors.append('Email jest wymagany')
        elif not self._is_valid_email(row['email']):
            errors.append('Nieprawidłowy format email')

        if not row.get('first_name'):
            errors.append('Imię jest wymagane')

        if not row.get('last_name'):
            errors.append('Nazwisko jest wymagane')

        if row.get('role') not in ('student', 'tutor', 'admin'):
            errors.append('Rola musi być: student, tutor lub admin')

        # Check for existing email
        if row.get('email') and User.objects.filter(email=row['email']).exists():
            errors.append('Użytkownik o tym email już istnieje')

        return errors

    def _is_valid_email(self, email: str) -> bool:
        """Validate email format using Django's validator."""
        try:
            validate_email(email)
            return True
        except ValidationError:
            return False

    @transaction.atomic
    def execute(self, send_emails: bool = True) -> Tuple[List[Dict], List[Dict]]:
        """Execute import and return (results, errors)."""
        from .forms import generate_temp_password
        from .models import UserCreationLog
        from .tasks import send_welcome_email_task

        results = []

        for row in self.valid_rows:
            try:
                temp_password = generate_temp_password()

                user = User.objects.create(
                    email=row['email'],
                    first_name=row['first_name'],
                    last_name=row['last_name'],
                    phone=row.get('phone', ''),
                    role=row['role'],
                    first_login=True,
                    is_profile_completed=False,
                )
                user.set_password(temp_password)
                user.save()

                # Create role-specific profile
                if row['role'] == 'student':
                    from apps.students.models import StudentProfile

                    StudentProfile.objects.create(
                        user=user,
                        class_name=row.get('class_name', ''),
                        parent_name=row.get('parent_name', ''),
                        parent_email=row.get('parent_email', ''),
                        parent_phone=row.get('parent_phone', ''),
                    )
                elif row['role'] == 'tutor':
                    from apps.tutors.models import TutorProfile

                    TutorProfile.objects.create(user=user)

                # Log creation
                UserCreationLog.objects.create(
                    created_user=user,
                    created_by=self.created_by,
                    email_sent=send_emails,
                )

                # Send email
                if send_emails:
                    send_welcome_email_task.delay(user.id, temp_password)

                results.append({
                    'email': user.email,
                    'user_id': user.id,
                    'temp_password': temp_password if not send_emails else None,
                })

            except Exception as e:
                logger.exception('Error importing user %s', row.get('email', 'unknown'))
                self.errors.append({
                    'row': row.get('email', 'unknown'),
                    'errors': [str(e)],
                })

        return results, self.errors


class UserArchiveService:
    """Service for archiving user data (GDPR compliance)."""

    # Default retention period in years
    DEFAULT_RETENTION_YEARS = 5

    def archive_user(
        self,
        user: User,
        reason: str,
        archived_by: User,
        notes: str = '',
        retention_years: int = None,
    ) -> Optional['UserArchive']:
        """Archive user data and deactivate account.

        Args:
            user: User to archive.
            reason: Reason for archiving.
            archived_by: Admin performing the archive.
            notes: Optional notes.
            retention_years: Years to retain data (default 5).

        Returns:
            Created UserArchive instance or None on error.
        """
        from .models import UserArchive

        if retention_years is None:
            retention_years = self.DEFAULT_RETENTION_YEARS

        try:
            # Collect user data
            user_data = self._collect_user_data(user)

            # Create email hash for reference
            email_hash = hashlib.sha256(user.email.encode()).hexdigest()

            # Calculate retention date
            retention_until = timezone.now().date() + timedelta(days=365 * retention_years)

            # Create archive
            archive = UserArchive.objects.create(
                original_user_id=user.id,
                email_hash=email_hash,
                archived_data=user_data,
                reason=reason,
                archived_by=archived_by,
                notes=notes,
                retention_until=retention_until,
            )

            # Deactivate user
            user.is_active = False
            user.save(update_fields=['is_active'])

            logger.info(
                'User %s archived by %s (reason: %s)',
                user.email,
                archived_by.email,
                reason,
            )

            return archive

        except Exception as e:
            logger.exception('Error archiving user %s: %s', user.email, e)
            return None

    def _collect_user_data(self, user: User) -> dict:
        """Collect all user data for archiving.

        Args:
            user: User whose data to collect.

        Returns:
            Dictionary with all user data.
        """
        data = {
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone': user.phone,
                'role': user.role,
                'date_joined': user.date_joined.isoformat(),
                'last_login': user.last_login.isoformat() if user.last_login else None,
            }
        }

        # Add student profile
        if hasattr(user, 'student_profile'):
            profile = user.student_profile
            data['student_profile'] = {
                'class_name': profile.class_name,
                'current_level': profile.current_level,
                'learning_goals': profile.learning_goals,
                'parent_name': profile.parent_name,
                'parent_email': profile.parent_email,
                'parent_phone': profile.parent_phone,
                'notes': profile.notes,
            }

        # Add tutor profile
        if hasattr(user, 'tutor_profile'):
            profile = user.tutor_profile
            data['tutor_profile'] = {
                'bio': profile.bio,
                'education': profile.education,
                'experience_years': profile.experience_years,
                'hourly_rate': str(profile.hourly_rate) if profile.hourly_rate else None,
            }

        # Add notification preferences
        if hasattr(user, 'notification_preferences'):
            prefs = user.notification_preferences
            data['notification_preferences'] = {
                'email_lesson_reminders': prefs.email_lesson_reminders,
                'email_messages': prefs.email_messages,
                'sms_urgent': prefs.sms_urgent,
            }

        return data

    def anonymize_archive(self, archive: 'UserArchive') -> None:
        """Anonymize archived data (for GDPR right to be forgotten).

        Args:
            archive: Archive to anonymize.
        """
        from .models import UserArchive

        if archive.is_anonymized:
            return

        # Replace personal data with anonymized placeholders
        anonymized_data = {
            'anonymized': True,
            'anonymized_at': timezone.now().isoformat(),
            'original_role': archive.archived_data.get('user', {}).get('role'),
            'archived_date': archive.created_at.isoformat(),
        }

        archive.archived_data = anonymized_data
        archive.is_anonymized = True
        archive.anonymized_at = timezone.now()
        archive.save(update_fields=['archived_data', 'is_anonymized', 'anonymized_at'])

        logger.info('Archive #%s anonymized', archive.id)

    def cleanup_expired_archives(self) -> int:
        """Delete archives past retention date.

        Returns:
            Number of deleted archives.
        """
        from .models import UserArchive

        expired = UserArchive.objects.filter(
            retention_until__lt=timezone.now().date(),
            is_anonymized=True,
        )

        count = expired.count()
        expired.delete()

        logger.info('Cleaned up %d expired archives', count)
        return count
