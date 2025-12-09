from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Q
from django.template.loader import render_to_string
from django.utils import timezone

from apps.accounts.models import NotificationPreference
from apps.accounts.models import User as UserModel
from apps.lessons.models import LessonStudent

from .models import (
    Announcement,
    Notification,
    NotificationPriority,
    NotificationType,
)

User = get_user_model()


class NotificationService:
    """Serwis do obsługi powiadomień."""

    NOTIFICATION_ICONS = {
        'SYSTEM': 'cog',
        'MESSAGE': 'chat',
        'EVENT': 'calendar',
        'ATTENDANCE': 'check-circle',
        'CANCELLATION': 'x-circle',
        'INVOICE': 'currency-dollar',
        'ANNOUNCEMENT': 'megaphone',
        'REMINDER': 'clock',
    }

    @classmethod
    @transaction.atomic
    def create_notification(
        cls,
        user,
        title: str,
        message: str,
        notification_type: str = NotificationType.SYSTEM,
        priority: str = NotificationPriority.NORMAL,
        action_url: str = '',
        action_label: str = '',
        related_entity_type: str = '',
        related_entity_id: str = '',
        send_email: bool = True,
        expires_at=None,
    ) -> Notification:
        """Tworzy powiadomienie dla użytkownika."""
        notification = Notification.objects.create(
            user=user,
            title=title,
            message=message,
            type=notification_type,
            priority=priority,
            action_url=action_url,
            action_label=action_label,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            expires_at=expires_at,
        )

        # Sprawdź preferencje i wyślij email
        if send_email:
            cls._maybe_send_email(notification)

        return notification

    @classmethod
    def _maybe_send_email(cls, notification: Notification) -> None:
        """Sprawdza preferencje i wysyła email jeśli dozwolone.

        Uses NotificationPreference from accounts app.
        """
        try:
            prefs = notification.user.notification_preferences
        except NotificationPreference.DoesNotExist:
            prefs = None

        # Sprawdź ciche godziny
        if prefs and cls._is_quiet_hours(prefs):
            return

        # Sprawdź typ powiadomienia
        type_enabled = cls._check_type_preference(notification.type, prefs)
        if not type_enabled:
            return

        # Wyślij email asynchronicznie
        from .tasks import send_notification_email

        send_notification_email.delay(str(notification.id))

    @classmethod
    def _is_quiet_hours(cls, prefs: NotificationPreference) -> bool:
        """Sprawdza czy teraz są ciche godziny."""
        if not prefs.quiet_hours_start or not prefs.quiet_hours_end:
            return False

        current_time = timezone.now().time()
        start = prefs.quiet_hours_start
        end = prefs.quiet_hours_end

        if start < end:
            return start <= current_time < end
        else:
            # Przypadek gdy cisza przechodzi przez północ (np. 22:00-7:00)
            return current_time >= start or current_time < end

    @classmethod
    def _check_type_preference(cls, notification_type: str, prefs) -> bool:
        """Sprawdza preferencje dla typu powiadomienia.

        Uses NotificationPreference from accounts app which has fields:
        - email_lesson_reminders, email_lesson_changes, email_messages
        - email_invoices, email_system, email_marketing
        """
        if not prefs:
            return True

        type_map = {
            'SYSTEM': prefs.email_system,
            'MESSAGE': prefs.email_messages,
            'EVENT': prefs.email_lesson_reminders,
            'ATTENDANCE': prefs.email_lesson_changes,
            'CANCELLATION': prefs.email_lesson_changes,
            'INVOICE': prefs.email_invoices,
            'ANNOUNCEMENT': prefs.email_system,
            'REMINDER': prefs.email_lesson_reminders,
        }

        return type_map.get(notification_type, True)

    @classmethod
    def get_user_notifications(cls, user, include_read: bool = False, limit: int = 50):
        """Pobiera powiadomienia użytkownika."""
        queryset = Notification.objects.filter(user=user, is_archived=False).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
        )

        if not include_read:
            queryset = queryset.filter(is_read=False)

        return queryset[:limit]

    @classmethod
    def get_unread_count(cls, user) -> int:
        """Pobiera liczbę nieprzeczytanych powiadomień."""
        return (
            Notification.objects.filter(user=user, is_read=False, is_archived=False)
            .filter(Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now()))
            .count()
        )

    @classmethod
    def mark_as_read(cls, notification_id: str, user) -> None:
        """Oznacza powiadomienie jako przeczytane."""
        Notification.objects.filter(id=notification_id, user=user).update(
            is_read=True, read_at=timezone.now()
        )

    @classmethod
    def mark_all_as_read(cls, user) -> None:
        """Oznacza wszystkie powiadomienia jako przeczytane."""
        Notification.objects.filter(user=user, is_read=False).update(
            is_read=True, read_at=timezone.now()
        )

    @classmethod
    def archive_notification(cls, notification_id: str, user) -> None:
        """Archiwizuje powiadomienie."""
        Notification.objects.filter(id=notification_id, user=user).update(
            is_archived=True, archived_at=timezone.now()
        )

    @classmethod
    def delete_notification(cls, notification_id: str, user) -> None:
        """Usuwa powiadomienie."""
        Notification.objects.filter(id=notification_id, user=user).delete()

    @classmethod
    def bulk_notify(cls, users, title: str, message: str, **kwargs) -> list[Notification]:
        """Wysyła powiadomienia do wielu użytkowników."""
        notifications = []
        for user in users:
            notification = cls.create_notification(
                user=user,
                title=title,
                message=message,
                **kwargs,
            )
            notifications.append(notification)

        return notifications

    @classmethod
    def notify_by_role(
        cls, roles: list, title: str, message: str, **kwargs
    ) -> list[Notification]:
        """Wysyła powiadomienia do użytkowników z określonymi rolami."""
        users = User.objects.filter(role__in=roles, is_active=True)
        return cls.bulk_notify(users, title, message, **kwargs)


class AnnouncementService:
    """Serwis do obsługi ogłoszeń."""

    @classmethod
    def create_announcement(
        cls,
        title: str,
        content: str,
        created_by,
        announcement_type: str = 'INFO',
        target_roles: list | None = None,
        is_pinned: bool = False,
        expires_at=None,
    ) -> Announcement:
        """Tworzy nowe ogłoszenie."""
        return Announcement.objects.create(
            title=title,
            content=content,
            type=announcement_type,
            target_roles=target_roles or [],
            is_pinned=is_pinned,
            expires_at=expires_at,
            created_by=created_by,
        )

    @classmethod
    def get_active_announcements(cls, user):
        """Pobiera aktywne ogłoszenia dla użytkownika."""
        now = timezone.now()

        queryset = Announcement.objects.filter(publish_at__lte=now).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=now)
        )

        # Filtruj po roli użytkownika
        if user.is_authenticated:
            # Filter announcements: show if target_roles is empty OR user's role is in list
            # Use icontains for string search in JSON array (works with SQLite)
            queryset = queryset.filter(
                Q(target_roles=[]) | Q(target_roles__icontains=user.role)
            )

        return queryset.order_by('-is_pinned', '-publish_at')

    @classmethod
    def delete_announcement(cls, announcement_id: str) -> None:
        """Usuwa ogłoszenie."""
        Announcement.objects.filter(id=announcement_id).delete()


class ParentNotificationService:
    """Service for parent notifications."""

    def send_absence_alert(self, student: UserModel, lesson) -> bool:
        """Send immediate absence alert to parent."""
        profile = getattr(student, 'student_profile', None)

        if not profile or not profile.parent_email:
            return False

        context = {
            'parent_name': profile.parent_name or 'Szanowni Rodzice',
            'student_name': student.get_full_name(),
            'lesson_title': lesson.title,
            'lesson_date': lesson.start_time.strftime('%d %B %Y'),
            'lesson_time': lesson.start_time.strftime('%H:%M'),
            'subject': lesson.subject.name,
            'tutor': lesson.tutor.get_full_name(),
        }

        html_content = render_to_string(
            'emails/absence_alert.html',
            context,
        )

        send_mail(
            subject=f'Alert: Nieobecnosc - {student.get_full_name()}',
            message='',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[profile.parent_email],
            html_message=html_content,
        )

        return True

    def send_weekly_summaries(self) -> int:
        """Send weekly attendance summaries to all parents."""
        week_start = timezone.now() - timedelta(days=7)
        week_end = timezone.now()

        students = (
            UserModel.objects.filter(
                role='STUDENT',
                is_active=True,
                student_profile__parent_email__isnull=False,
            )
            .exclude(student_profile__parent_email='')
            .select_related('student_profile')
        )

        sent_count = 0

        for student in students:
            profile = student.student_profile

            # Get week's attendance
            records = LessonStudent.objects.filter(
                student=student,
                lesson__start_time__gte=week_start,
                lesson__start_time__lte=week_end,
            ).select_related('lesson', 'lesson__subject')

            if not records.exists():
                continue

            total = records.count()
            present = records.filter(attendance_status='PRESENT').count()
            late = records.filter(attendance_status='LATE').count()
            absent = records.filter(attendance_status='ABSENT').count()
            rate = round(((present + late) / total * 100), 1) if total > 0 else 0

            context = {
                'parent_name': profile.parent_name or 'Szanowni Rodzice',
                'student_name': student.get_full_name(),
                'week_start': week_start.strftime('%d %b'),
                'week_end': week_end.strftime('%d %b %Y'),
                'total_lessons': total,
                'present_count': present,
                'late_count': late,
                'absent_count': absent,
                'attendance_rate': rate,
                'lessons': [
                    {
                        'date': r.lesson.start_time.strftime('%d.%m.%Y'),
                        'subject': r.lesson.subject.name,
                        'status': self._get_status_label(r.attendance_status),
                    }
                    for r in records.order_by('lesson__start_time')
                ],
            }

            html_content = render_to_string(
                'emails/weekly_summary.html',
                context,
            )

            send_mail(
                subject=f'Podsumowanie tygodnia - {student.get_full_name()}',
                message='',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[profile.parent_email],
                html_message=html_content,
            )

            sent_count += 1

        return sent_count

    def _get_status_label(self, status: str) -> str:
        """Get Polish label for status."""
        labels = {
            'PRESENT': 'Obecny',
            'LATE': 'Spóźniony',
            'ABSENT': 'Nieobecny',
            'EXCUSED': 'Usprawiedliwiony',
        }
        return labels.get(status, 'Oczekujące')


parent_notification_service = ParentNotificationService()
