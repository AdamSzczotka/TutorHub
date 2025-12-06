# Phase 8 - Sprint 8.2: Notifications System (Django)

## Tasks 103-107: Comprehensive Notification Platform

> **Duration**: Week 12 (Days 4-5)
> **Goal**: Complete notification system with email queue, preferences, announcements, and polling
> **Dependencies**: Sprint 8.1 completed (Messaging System)

---

## SPRINT OVERVIEW

| Task ID | Description                     | Priority | Dependencies |
| ------- | ------------------------------- | -------- | ------------ |
| 103     | Notification center with badge  | Critical | Task 102     |
| 104     | Email queue with Celery         | Critical | Task 103     |
| 105     | Notification preferences        | High     | Task 104     |
| 106     | Announcements system            | High     | Task 105     |
| 107     | HTMX polling for real-time      | High     | Task 106     |

---

## NOTIFICATION MODELS

### Notification and Preference Models

**File**: `apps/notifications/models.py`

```python
import uuid
from django.db import models
from django.conf import settings


class NotificationType(models.TextChoices):
    SYSTEM = 'SYSTEM', 'Systemowe'
    MESSAGE = 'MESSAGE', 'Wiadomość'
    EVENT = 'EVENT', 'Wydarzenie'
    ATTENDANCE = 'ATTENDANCE', 'Obecność'
    CANCELLATION = 'CANCELLATION', 'Anulowanie'
    INVOICE = 'INVOICE', 'Faktura'
    ANNOUNCEMENT = 'ANNOUNCEMENT', 'Ogłoszenie'
    REMINDER = 'REMINDER', 'Przypomnienie'


class NotificationPriority(models.TextChoices):
    LOW = 'LOW', 'Niski'
    NORMAL = 'NORMAL', 'Normalny'
    HIGH = 'HIGH', 'Wysoki'
    URGENT = 'URGENT', 'Pilny'


class DigestFrequency(models.TextChoices):
    INSTANT = 'INSTANT', 'Natychmiastowe'
    HOURLY = 'HOURLY', 'Co godzinę'
    DAILY = 'DAILY', 'Raz dziennie'
    WEEKLY = 'WEEKLY', 'Raz w tygodniu'


class Notification(models.Model):
    """Model powiadomienia."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )

    # Content
    title = models.CharField('Tytuł', max_length=200)
    message = models.TextField('Treść')
    type = models.CharField(
        'Typ',
        max_length=20,
        choices=NotificationType.choices,
        default=NotificationType.SYSTEM
    )
    priority = models.CharField(
        'Priorytet',
        max_length=20,
        choices=NotificationPriority.choices,
        default=NotificationPriority.NORMAL
    )

    # Action/Link
    action_url = models.CharField('URL akcji', max_length=500, blank=True)
    action_label = models.CharField('Etykieta akcji', max_length=50, blank=True)

    # Related entities
    related_entity_type = models.CharField(
        'Typ powiązanego obiektu',
        max_length=50,
        blank=True
    )
    related_entity_id = models.CharField(
        'ID powiązanego obiektu',
        max_length=50,
        blank=True
    )

    # Status
    is_read = models.BooleanField('Przeczytane', default=False)
    read_at = models.DateTimeField('Przeczytano', null=True, blank=True)
    is_archived = models.BooleanField('Zarchiwizowane', default=False)
    archived_at = models.DateTimeField('Zarchiwizowano', null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField('Wygasa', null=True, blank=True)

    class Meta:
        db_table = 'notifications'
        verbose_name = 'Powiadomienie'
        verbose_name_plural = 'Powiadomienia'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', '-created_at']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['type', 'priority']),
        ]

    def __str__(self):
        return f"{self.title} - {self.user}"


class NotificationPreference(models.Model):
    """Preferencje powiadomień użytkownika."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_preferences'
    )

    # Channel preferences
    email_enabled = models.BooleanField('Email włączony', default=True)
    push_enabled = models.BooleanField('Push włączony', default=True)
    sms_enabled = models.BooleanField('SMS włączony', default=False)

    # Event notifications
    event_reminders = models.BooleanField('Przypomnienia o zajęciach', default=True)
    event_changes = models.BooleanField('Zmiany w zajęciach', default=True)
    event_cancellations = models.BooleanField('Anulowania zajęć', default=True)

    # Attendance notifications
    attendance_marked = models.BooleanField('Obecność oznaczona', default=True)
    absence_alerts = models.BooleanField('Alerty nieobecności', default=True)

    # Cancellation notifications
    cancellation_requests = models.BooleanField('Prośby o anulowanie', default=True)
    cancellation_approvals = models.BooleanField('Zatwierdzenia anulowań', default=True)

    # Invoice notifications
    invoice_generated = models.BooleanField('Nowa faktura', default=True)
    payment_reminders = models.BooleanField('Przypomnienia o płatności', default=True)
    payment_overdue = models.BooleanField('Płatność przeterminowana', default=True)

    # Message notifications
    new_messages = models.BooleanField('Nowe wiadomości', default=True)
    message_replies = models.BooleanField('Odpowiedzi na wiadomości', default=True)

    # System notifications
    announcements = models.BooleanField('Ogłoszenia', default=True)
    system_updates = models.BooleanField('Aktualizacje systemu', default=False)

    # Frequency settings
    digest_frequency = models.CharField(
        'Częstotliwość',
        max_length=20,
        choices=DigestFrequency.choices,
        default=DigestFrequency.INSTANT
    )
    quiet_hours_start = models.PositiveSmallIntegerField(
        'Cisza od (godzina)',
        null=True,
        blank=True
    )
    quiet_hours_end = models.PositiveSmallIntegerField(
        'Cisza do (godzina)',
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'notification_preferences'
        verbose_name = 'Preferencje powiadomień'
        verbose_name_plural = 'Preferencje powiadomień'


class AnnouncementType(models.TextChoices):
    INFO = 'INFO', 'Informacja'
    WARNING = 'WARNING', 'Ostrzeżenie'
    SUCCESS = 'SUCCESS', 'Sukces'
    ERROR = 'ERROR', 'Błąd'


class Announcement(models.Model):
    """Model ogłoszenia systemowego."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Content
    title = models.CharField('Tytuł', max_length=200)
    content = models.TextField('Treść')
    type = models.CharField(
        'Typ',
        max_length=20,
        choices=AnnouncementType.choices,
        default=AnnouncementType.INFO
    )

    # Targeting
    target_roles = models.JSONField(
        'Role docelowe',
        default=list,
        help_text='Lista ról, dla których jest widoczne'
    )
    is_pinned = models.BooleanField('Przypięte', default=False)

    # Scheduling
    publish_at = models.DateTimeField('Data publikacji', auto_now_add=True)
    expires_at = models.DateTimeField('Data wygaśnięcia', null=True, blank=True)

    # Metadata
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_announcements'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'announcements'
        verbose_name = 'Ogłoszenie'
        verbose_name_plural = 'Ogłoszenia'
        ordering = ['-is_pinned', '-publish_at']
        indexes = [
            models.Index(fields=['publish_at', 'expires_at']),
            models.Index(fields=['is_pinned']),
        ]

    def __str__(self):
        return self.title
```

---

## NOTIFICATION SERVICE

### Core Notification Service

**File**: `apps/notifications/services.py`

```python
from django.db import transaction
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth import get_user_model

from .models import (
    Notification, NotificationPreference, Announcement,
    NotificationType, NotificationPriority
)
from .tasks import send_notification_email

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
        expires_at=None
    ):
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
            expires_at=expires_at
        )

        # Sprawdź preferencje i wyślij email
        if send_email:
            cls._maybe_send_email(notification)

        return notification

    @classmethod
    def _maybe_send_email(cls, notification):
        """Sprawdza preferencje i wysyła email jeśli dozwolone."""

        try:
            prefs = notification.user.notification_preferences
        except NotificationPreference.DoesNotExist:
            # Domyślnie wyślij email
            prefs = None

        # Sprawdź czy email jest włączony
        if prefs and not prefs.email_enabled:
            return

        # Sprawdź ciche godziny
        if prefs and cls._is_quiet_hours(prefs):
            return

        # Sprawdź częstotliwość (dla natychmiastowych wysyłamy od razu)
        if prefs and prefs.digest_frequency != 'INSTANT':
            return

        # Sprawdź typ powiadomienia
        type_enabled = cls._check_type_preference(notification.type, prefs)
        if not type_enabled:
            return

        # Wyślij email asynchronicznie
        send_notification_email.delay(str(notification.id))

    @classmethod
    def _is_quiet_hours(cls, prefs):
        """Sprawdza czy teraz są ciche godziny."""

        if not prefs.quiet_hours_start or not prefs.quiet_hours_end:
            return False

        current_hour = timezone.now().hour

        start = prefs.quiet_hours_start
        end = prefs.quiet_hours_end

        if start < end:
            return start <= current_hour < end
        else:
            # Przypadek gdy cisza przechodzi przez północ (np. 22-7)
            return current_hour >= start or current_hour < end

    @classmethod
    def _check_type_preference(cls, notification_type, prefs):
        """Sprawdza preferencje dla typu powiadomienia."""

        if not prefs:
            return True

        type_map = {
            'SYSTEM': True,  # Systemowe zawsze włączone
            'MESSAGE': prefs.new_messages,
            'EVENT': prefs.event_reminders,
            'ATTENDANCE': prefs.attendance_marked,
            'CANCELLATION': prefs.cancellation_requests,
            'INVOICE': prefs.invoice_generated,
            'ANNOUNCEMENT': prefs.announcements,
            'REMINDER': prefs.event_reminders,
        }

        return type_map.get(notification_type, True)

    @classmethod
    def get_user_notifications(cls, user, include_read=False, limit=50):
        """Pobiera powiadomienia użytkownika."""

        queryset = Notification.objects.filter(
            user=user,
            is_archived=False
        ).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
        )

        if not include_read:
            queryset = queryset.filter(is_read=False)

        return queryset[:limit]

    @classmethod
    def get_unread_count(cls, user):
        """Pobiera liczbę nieprzeczytanych powiadomień."""

        return Notification.objects.filter(
            user=user,
            is_read=False,
            is_archived=False
        ).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
        ).count()

    @classmethod
    def mark_as_read(cls, notification_id, user):
        """Oznacza powiadomienie jako przeczytane."""

        Notification.objects.filter(
            id=notification_id,
            user=user
        ).update(
            is_read=True,
            read_at=timezone.now()
        )

    @classmethod
    def mark_all_as_read(cls, user):
        """Oznacza wszystkie powiadomienia jako przeczytane."""

        Notification.objects.filter(
            user=user,
            is_read=False
        ).update(
            is_read=True,
            read_at=timezone.now()
        )

    @classmethod
    def archive_notification(cls, notification_id, user):
        """Archiwizuje powiadomienie."""

        Notification.objects.filter(
            id=notification_id,
            user=user
        ).update(
            is_archived=True,
            archived_at=timezone.now()
        )

    @classmethod
    def delete_notification(cls, notification_id, user):
        """Usuwa powiadomienie."""

        Notification.objects.filter(
            id=notification_id,
            user=user
        ).delete()

    @classmethod
    def bulk_notify(cls, users, title, message, **kwargs):
        """Wysyła powiadomienia do wielu użytkowników."""

        notifications = []
        for user in users:
            notification = cls.create_notification(
                user=user,
                title=title,
                message=message,
                **kwargs
            )
            notifications.append(notification)

        return notifications

    @classmethod
    def notify_by_role(cls, roles: list, title: str, message: str, **kwargs):
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
        target_roles: list = None,
        is_pinned: bool = False,
        expires_at=None
    ):
        """Tworzy nowe ogłoszenie."""

        return Announcement.objects.create(
            title=title,
            content=content,
            type=announcement_type,
            target_roles=target_roles or [],
            is_pinned=is_pinned,
            expires_at=expires_at,
            created_by=created_by
        )

    @classmethod
    def get_active_announcements(cls, user):
        """Pobiera aktywne ogłoszenia dla użytkownika."""

        now = timezone.now()

        queryset = Announcement.objects.filter(
            publish_at__lte=now
        ).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=now)
        )

        # Filtruj po roli użytkownika
        if user.is_authenticated:
            queryset = queryset.filter(
                Q(target_roles=[]) |
                Q(target_roles__contains=[user.role])
            )

        return queryset.order_by('-is_pinned', '-publish_at')

    @classmethod
    def delete_announcement(cls, announcement_id):
        """Usuwa ogłoszenie."""

        Announcement.objects.filter(id=announcement_id).delete()
```

---

## CELERY TASKS

### Email Notification Tasks

**File**: `apps/notifications/tasks.py`

```python
from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone

from .models import Notification, NotificationPreference, DigestFrequency


@shared_task
def send_notification_email(notification_id: str):
    """Wysyła email z powiadomieniem."""

    try:
        notification = Notification.objects.select_related('user').get(
            id=notification_id
        )
    except Notification.DoesNotExist:
        return

    user = notification.user

    # Renderuj szablon email
    html_content = render_to_string(
        'notifications/email/notification.html',
        {
            'notification': notification,
            'user': user,
            'site_url': settings.SITE_URL,
        }
    )

    # Wyślij email
    send_mail(
        subject=notification.title,
        message=notification.message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_content,
        fail_silently=False
    )


@shared_task
def send_hourly_digest():
    """Wysyła godzinne podsumowanie powiadomień."""

    _send_digest(DigestFrequency.HOURLY)


@shared_task
def send_daily_digest():
    """Wysyła dzienne podsumowanie powiadomień."""

    _send_digest(DigestFrequency.DAILY)


@shared_task
def send_weekly_digest():
    """Wysyła tygodniowe podsumowanie powiadomień."""

    _send_digest(DigestFrequency.WEEKLY)


def _send_digest(frequency: str):
    """Wysyła podsumowanie dla określonej częstotliwości."""

    from django.contrib.auth import get_user_model
    User = get_user_model()

    # Znajdź użytkowników z tą częstotliwością
    users = User.objects.filter(
        notification_preferences__digest_frequency=frequency,
        notification_preferences__email_enabled=True,
        is_active=True
    )

    # Określ zakres czasowy
    now = timezone.now()
    if frequency == DigestFrequency.HOURLY:
        start_time = now - timezone.timedelta(hours=1)
    elif frequency == DigestFrequency.DAILY:
        start_time = now - timezone.timedelta(days=1)
    else:  # WEEKLY
        start_time = now - timezone.timedelta(weeks=1)

    for user in users:
        notifications = Notification.objects.filter(
            user=user,
            created_at__gte=start_time,
            is_read=False
        ).order_by('-created_at')

        if not notifications.exists():
            continue

        html_content = render_to_string(
            'notifications/email/digest.html',
            {
                'user': user,
                'notifications': notifications,
                'frequency': frequency,
                'site_url': settings.SITE_URL,
            }
        )

        send_mail(
            subject=f'Podsumowanie powiadomień - Na Piątkę',
            message=f'Masz {notifications.count()} nieprzeczytanych powiadomień.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_content,
            fail_silently=True
        )


@shared_task
def cleanup_expired_notifications():
    """Usuwa wygasłe powiadomienia."""

    now = timezone.now()

    # Usuń wygasłe powiadomienia starsze niż 30 dni
    old_date = now - timezone.timedelta(days=30)

    Notification.objects.filter(
        expires_at__lt=now,
        created_at__lt=old_date
    ).delete()

    # Archiwizuj przeczytane powiadomienia starsze niż 7 dni
    week_ago = now - timezone.timedelta(days=7)

    Notification.objects.filter(
        is_read=True,
        is_archived=False,
        read_at__lt=week_ago
    ).update(is_archived=True)
```

### Celery Beat Schedule

**File**: `napiatke/celery.py` (dodatek)

```python
# Dodaj do konfiguracji Celery Beat

app.conf.beat_schedule.update({
    'send-hourly-digest': {
        'task': 'apps.notifications.tasks.send_hourly_digest',
        'schedule': crontab(minute=0),  # Co godzinę
    },
    'send-daily-digest': {
        'task': 'apps.notifications.tasks.send_daily_digest',
        'schedule': crontab(hour=8, minute=0),  # Codziennie o 8:00
    },
    'send-weekly-digest': {
        'task': 'apps.notifications.tasks.send_weekly_digest',
        'schedule': crontab(hour=8, minute=0, day_of_week=1),  # Poniedziałki o 8:00
    },
    'cleanup-expired-notifications': {
        'task': 'apps.notifications.tasks.cleanup_expired_notifications',
        'schedule': crontab(hour=3, minute=0),  # Codziennie o 3:00
    },
})
```

---

## NOTIFICATION VIEWS

### Notification Views

**File**: `apps/notifications/views.py`

```python
from django.views.generic import ListView, View, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.shortcuts import redirect

from apps.core.mixins import HTMXMixin, AdminRequiredMixin
from .models import Notification, NotificationPreference, Announcement
from .services import NotificationService, AnnouncementService
from .forms import NotificationPreferenceForm, AnnouncementForm


class NotificationListView(LoginRequiredMixin, HTMXMixin, ListView):
    """Lista powiadomień użytkownika."""

    template_name = 'notifications/list.html'
    partial_template_name = 'notifications/partials/_notification_list.html'
    context_object_name = 'notifications'
    paginate_by = 20

    def get_queryset(self):
        include_read = self.request.GET.get('all') == 'true'
        return NotificationService.get_user_notifications(
            self.request.user,
            include_read=include_read,
            limit=100
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['unread_count'] = NotificationService.get_unread_count(
            self.request.user
        )
        return context


class NotificationDropdownView(LoginRequiredMixin, View):
    """Dropdown z powiadomieniami (dla nagłówka)."""

    def get(self, request):
        notifications = NotificationService.get_user_notifications(
            request.user,
            include_read=False,
            limit=10
        )
        unread_count = NotificationService.get_unread_count(request.user)

        html = render_to_string(
            'notifications/partials/_dropdown.html',
            {
                'notifications': notifications,
                'unread_count': unread_count,
            },
            request=request
        )

        return HttpResponse(html)


class UnreadCountView(LoginRequiredMixin, View):
    """Zwraca liczbę nieprzeczytanych powiadomień."""

    def get(self, request):
        count = NotificationService.get_unread_count(request.user)

        if request.headers.get('HX-Request'):
            return HttpResponse(
                render_to_string(
                    'notifications/partials/_badge.html',
                    {'count': count},
                    request=request
                )
            )

        return JsonResponse({'count': count})


class MarkAsReadView(LoginRequiredMixin, View):
    """Oznacza powiadomienie jako przeczytane."""

    def post(self, request, notification_id):
        NotificationService.mark_as_read(notification_id, request.user)

        return HttpResponse(
            status=204,
            headers={'HX-Trigger': 'notificationRead'}
        )


class MarkAllAsReadView(LoginRequiredMixin, View):
    """Oznacza wszystkie powiadomienia jako przeczytane."""

    def post(self, request):
        NotificationService.mark_all_as_read(request.user)

        return HttpResponse(
            status=204,
            headers={'HX-Trigger': 'allNotificationsRead'}
        )


class ArchiveNotificationView(LoginRequiredMixin, View):
    """Archiwizuje powiadomienie."""

    def post(self, request, notification_id):
        NotificationService.archive_notification(notification_id, request.user)

        return HttpResponse(
            status=204,
            headers={'HX-Trigger': 'notificationArchived'}
        )


class DeleteNotificationView(LoginRequiredMixin, View):
    """Usuwa powiadomienie."""

    def delete(self, request, notification_id):
        NotificationService.delete_notification(notification_id, request.user)

        return HttpResponse(
            status=204,
            headers={'HX-Trigger': 'notificationDeleted'}
        )


class NotificationPreferencesView(LoginRequiredMixin, TemplateView):
    """Ustawienia powiadomień użytkownika."""

    template_name = 'notifications/preferences.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        prefs, _ = NotificationPreference.objects.get_or_create(
            user=self.request.user
        )
        context['form'] = NotificationPreferenceForm(instance=prefs)

        return context

    def post(self, request):
        prefs, _ = NotificationPreference.objects.get_or_create(
            user=request.user
        )
        form = NotificationPreferenceForm(request.POST, instance=prefs)

        if form.is_valid():
            form.save()

            if request.headers.get('HX-Request'):
                return HttpResponse(
                    status=204,
                    headers={'HX-Trigger': 'preferencesSaved'}
                )

            return redirect('notifications:preferences')

        return self.render_to_response({'form': form})


# ========== ANNOUNCEMENTS ==========

class AnnouncementBannerView(LoginRequiredMixin, View):
    """Wyświetla aktywne ogłoszenia."""

    def get(self, request):
        announcements = AnnouncementService.get_active_announcements(
            request.user
        )

        html = render_to_string(
            'notifications/partials/_announcement_banner.html',
            {'announcements': announcements},
            request=request
        )

        return HttpResponse(html)


class AnnouncementListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    """Lista ogłoszeń (admin)."""

    model = Announcement
    template_name = 'admin_panel/announcements/list.html'
    context_object_name = 'announcements'
    paginate_by = 20


class CreateAnnouncementView(LoginRequiredMixin, AdminRequiredMixin, View):
    """Tworzy nowe ogłoszenie."""

    def get(self, request):
        form = AnnouncementForm()
        return HttpResponse(
            render_to_string(
                'admin_panel/announcements/partials/_form.html',
                {'form': form},
                request=request
            )
        )

    def post(self, request):
        form = AnnouncementForm(request.POST)

        if form.is_valid():
            announcement = AnnouncementService.create_announcement(
                title=form.cleaned_data['title'],
                content=form.cleaned_data['content'],
                created_by=request.user,
                announcement_type=form.cleaned_data['type'],
                target_roles=form.cleaned_data.get('target_roles', []),
                is_pinned=form.cleaned_data.get('is_pinned', False),
                expires_at=form.cleaned_data.get('expires_at')
            )

            # Powiadom użytkowników
            if form.cleaned_data.get('notify_users'):
                NotificationService.notify_by_role(
                    roles=form.cleaned_data.get('target_roles', []),
                    title=announcement.title,
                    message=announcement.content[:200],
                    notification_type='ANNOUNCEMENT',
                    action_url='/announcements/',
                    action_label='Zobacz ogłoszenie'
                )

            return HttpResponse(
                status=204,
                headers={'HX-Trigger': 'announcementCreated'}
            )

        return HttpResponse(
            render_to_string(
                'admin_panel/announcements/partials/_form.html',
                {'form': form},
                request=request
            ),
            status=400
        )


class DeleteAnnouncementView(LoginRequiredMixin, AdminRequiredMixin, View):
    """Usuwa ogłoszenie."""

    def delete(self, request, announcement_id):
        AnnouncementService.delete_announcement(announcement_id)

        return HttpResponse(
            status=204,
            headers={'HX-Trigger': 'announcementDeleted'}
        )
```

---

## NOTIFICATION FORMS

**File**: `apps/notifications/forms.py`

```python
from django import forms
from django.contrib.auth import get_user_model

from .models import (
    NotificationPreference, Announcement,
    DigestFrequency, AnnouncementType
)

User = get_user_model()


class NotificationPreferenceForm(forms.ModelForm):
    """Formularz preferencji powiadomień."""

    class Meta:
        model = NotificationPreference
        exclude = ['id', 'user', 'created_at', 'updated_at']
        widgets = {
            'digest_frequency': forms.Select(attrs={
                'class': 'select select-bordered w-full'
            }),
            'quiet_hours_start': forms.Select(
                choices=[(None, 'Wyłączone')] + [(i, f'{i:02d}:00') for i in range(24)],
                attrs={'class': 'select select-bordered w-full'}
            ),
            'quiet_hours_end': forms.Select(
                choices=[(None, 'Wyłączone')] + [(i, f'{i:02d}:00') for i in range(24)],
                attrs={'class': 'select select-bordered w-full'}
            ),
        }


class AnnouncementForm(forms.Form):
    """Formularz tworzenia ogłoszenia."""

    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'Tytuł ogłoszenia'
        }),
        label='Tytuł'
    )
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'textarea textarea-bordered w-full',
            'rows': 5,
            'placeholder': 'Treść ogłoszenia'
        }),
        label='Treść'
    )
    type = forms.ChoiceField(
        choices=AnnouncementType.choices,
        initial=AnnouncementType.INFO,
        widget=forms.Select(attrs={
            'class': 'select select-bordered w-full'
        }),
        label='Typ'
    )
    target_roles = forms.MultipleChoiceField(
        choices=[
            ('ADMIN', 'Administratorzy'),
            ('TUTOR', 'Korepetytorzy'),
            ('STUDENT', 'Uczniowie'),
        ],
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'checkbox'
        }),
        label='Widoczne dla',
        help_text='Zostaw puste aby wyświetlić wszystkim'
    )
    is_pinned = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'checkbox'
        }),
        label='Przypnij na górze'
    )
    expires_at = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={
            'class': 'input input-bordered w-full',
            'type': 'datetime-local'
        }),
        label='Data wygaśnięcia'
    )
    notify_users = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'checkbox'
        }),
        label='Wyślij powiadomienie do użytkowników'
    )
```

---

## NOTIFICATION TEMPLATES

### Notification Center Template

**File**: `templates/notifications/partials/_dropdown.html`

```html
<div class="dropdown dropdown-end"
     hx-get="{% url 'notifications:unread_count' %}"
     hx-trigger="every 30s"
     hx-target="#notification-badge"
     hx-swap="innerHTML">

    <label tabindex="0" class="btn btn-ghost btn-circle">
        <div class="indicator">
            <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"></path>
            </svg>
            <span id="notification-badge">
                {% include "notifications/partials/_badge.html" %}
            </span>
        </div>
    </label>

    <div tabindex="0" class="dropdown-content card card-compact w-96 bg-base-100 shadow-xl z-50">
        <div class="card-body">
            <div class="flex items-center justify-between mb-2">
                <h3 class="font-bold">Powiadomienia</h3>
                {% if unread_count > 0 %}
                <button class="btn btn-ghost btn-xs"
                        hx-post="{% url 'notifications:mark_all_read' %}"
                        hx-swap="none">
                    Oznacz wszystkie
                </button>
                {% endif %}
            </div>

            <div class="divide-y max-h-96 overflow-y-auto">
                {% if notifications %}
                    {% for notification in notifications %}
                    {% include "notifications/partials/_notification_item.html" %}
                    {% endfor %}
                {% else %}
                <div class="py-8 text-center text-gray-500">
                    <svg class="mx-auto h-8 w-8 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"></path>
                    </svg>
                    <p class="text-sm">Brak nowych powiadomień</p>
                </div>
                {% endif %}
            </div>

            {% if notifications %}
            <div class="card-actions justify-center pt-2 border-t">
                <a href="{% url 'notifications:list' %}" class="btn btn-ghost btn-sm">
                    Zobacz wszystkie
                </a>
            </div>
            {% endif %}
        </div>
    </div>
</div>
```

### Notification Item Template

**File**: `templates/notifications/partials/_notification_item.html`

```html
{% load humanize %}

<div class="py-3 px-2 hover:bg-gray-50 transition-colors group {% if not notification.is_read %}bg-blue-50/50{% endif %}"
     id="notification-{{ notification.id }}">
    <div class="flex items-start space-x-3">
        <!-- Icon -->
        <div class="flex-shrink-0 text-xl">
            {% if notification.type == 'SYSTEM' %}⚙️{% endif %}
            {% if notification.type == 'MESSAGE' %}💬{% endif %}
            {% if notification.type == 'EVENT' %}📅{% endif %}
            {% if notification.type == 'ATTENDANCE' %}✅{% endif %}
            {% if notification.type == 'CANCELLATION' %}🚫{% endif %}
            {% if notification.type == 'INVOICE' %}💰{% endif %}
            {% if notification.type == 'ANNOUNCEMENT' %}📢{% endif %}
            {% if notification.type == 'REMINDER' %}⏰{% endif %}
        </div>

        <!-- Content -->
        <div class="flex-1 min-w-0">
            <div class="flex items-start justify-between">
                <h4 class="font-medium text-sm truncate">
                    {{ notification.title }}
                </h4>
                {% if not notification.is_read %}
                <div class="h-2 w-2 rounded-full bg-blue-500 ml-2 flex-shrink-0"></div>
                {% endif %}
            </div>

            <p class="text-sm text-gray-600 line-clamp-2 mt-1">
                {{ notification.message }}
            </p>

            <div class="flex items-center justify-between mt-2">
                <span class="text-xs text-gray-500">
                    {{ notification.created_at|timesince }} temu
                </span>

                {% if notification.priority == 'HIGH' %}
                <span class="badge badge-warning badge-xs">Ważne</span>
                {% elif notification.priority == 'URGENT' %}
                <span class="badge badge-error badge-xs">Pilne</span>
                {% endif %}
            </div>

            {% if notification.action_url and notification.action_label %}
            <a href="{{ notification.action_url }}"
               class="text-sm text-primary hover:underline mt-1 inline-block"
               hx-post="{% url 'notifications:mark_read' notification.id %}"
               hx-swap="none">
                {{ notification.action_label }} →
            </a>
            {% endif %}
        </div>

        <!-- Actions (visible on hover) -->
        <div class="flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity flex space-x-1">
            {% if not notification.is_read %}
            <button class="btn btn-ghost btn-xs"
                    hx-post="{% url 'notifications:mark_read' notification.id %}"
                    hx-target="#notification-{{ notification.id }}"
                    hx-swap="outerHTML"
                    title="Oznacz jako przeczytane">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                </svg>
            </button>
            {% endif %}

            <button class="btn btn-ghost btn-xs"
                    hx-post="{% url 'notifications:archive' notification.id %}"
                    hx-target="#notification-{{ notification.id }}"
                    hx-swap="delete"
                    title="Archiwizuj">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4"></path>
                </svg>
            </button>

            <button class="btn btn-ghost btn-xs text-error"
                    hx-delete="{% url 'notifications:delete' notification.id %}"
                    hx-target="#notification-{{ notification.id }}"
                    hx-swap="delete"
                    hx-confirm="Czy na pewno chcesz usunąć?"
                    title="Usuń">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                </svg>
            </button>
        </div>
    </div>
</div>
```

### Badge Template

**File**: `templates/notifications/partials/_badge.html`

```html
{% if count > 0 %}
<span class="badge badge-primary badge-sm">
    {% if count > 99 %}99+{% else %}{{ count }}{% endif %}
</span>
{% endif %}
```

### Announcement Banner Template

**File**: `templates/notifications/partials/_announcement_banner.html`

```html
{% if announcements %}
<div class="space-y-2" x-data="{ dismissed: [] }">
    {% for announcement in announcements %}
    <div x-show="!dismissed.includes('{{ announcement.id }}')"
         x-transition
         class="alert {% if announcement.type == 'INFO' %}alert-info{% elif announcement.type == 'WARNING' %}alert-warning{% elif announcement.type == 'SUCCESS' %}alert-success{% else %}alert-error{% endif %}">

        <div class="flex-1">
            <div class="flex items-center space-x-2">
                {% if announcement.is_pinned %}
                <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M5 5a2 2 0 012-2h6a2 2 0 012 2v2H5V5z"></path>
                    <path fill-rule="evenodd" d="M10 18a.75.75 0 01-.75-.75V13H5.75a.75.75 0 010-1.5H10V8a.75.75 0 011.5 0v3.5h4.25a.75.75 0 010 1.5H11.5v4.25a.75.75 0 01-.75.75z" clip-rule="evenodd"></path>
                </svg>
                {% endif %}
                <h3 class="font-bold">{{ announcement.title }}</h3>
            </div>
            <p class="text-sm mt-1">{{ announcement.content }}</p>
        </div>

        <button @click="dismissed.push('{{ announcement.id }}')"
                class="btn btn-ghost btn-sm btn-circle">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
        </button>
    </div>
    {% endfor %}
</div>
{% endif %}
```

### Preferences Form Template

**File**: `templates/notifications/preferences.html`

```html
{% extends "base.html" %}

{% block content %}
<div class="max-w-3xl mx-auto p-6">
    <h1 class="text-2xl font-bold mb-6">Ustawienia powiadomień</h1>

    <form hx-post="{% url 'notifications:preferences' %}"
          hx-swap="none"
          hx-on::after-request="if(event.detail.successful) { alert('Zapisano!') }">
        {% csrf_token %}

        <!-- Kanały -->
        <div class="card bg-base-100 shadow mb-6">
            <div class="card-body">
                <h2 class="card-title">Kanały powiadomień</h2>
                <p class="text-gray-600 text-sm mb-4">
                    Wybierz sposób otrzymywania powiadomień
                </p>

                <div class="space-y-4">
                    <label class="flex items-center justify-between">
                        <div>
                            <span class="font-medium">Email</span>
                            <p class="text-sm text-gray-500">Otrzymuj powiadomienia na email</p>
                        </div>
                        <input type="checkbox"
                               name="email_enabled"
                               {% if form.instance.email_enabled %}checked{% endif %}
                               class="toggle toggle-primary">
                    </label>

                    <label class="flex items-center justify-between">
                        <div>
                            <span class="font-medium">Push (przeglądarka)</span>
                            <p class="text-sm text-gray-500">Powiadomienia push w przeglądarce</p>
                        </div>
                        <input type="checkbox"
                               name="push_enabled"
                               {% if form.instance.push_enabled %}checked{% endif %}
                               class="toggle toggle-primary">
                    </label>
                </div>
            </div>
        </div>

        <!-- Typy powiadomień -->
        <div class="card bg-base-100 shadow mb-6">
            <div class="card-body">
                <h2 class="card-title">Powiadomienia o zajęciach</h2>

                <div class="space-y-3">
                    <label class="flex items-center justify-between">
                        <span>Przypomnienia o zajęciach</span>
                        <input type="checkbox"
                               name="event_reminders"
                               {% if form.instance.event_reminders %}checked{% endif %}
                               class="toggle toggle-primary toggle-sm">
                    </label>

                    <label class="flex items-center justify-between">
                        <span>Zmiany w zajęciach</span>
                        <input type="checkbox"
                               name="event_changes"
                               {% if form.instance.event_changes %}checked{% endif %}
                               class="toggle toggle-primary toggle-sm">
                    </label>

                    <label class="flex items-center justify-between">
                        <span>Anulowania zajęć</span>
                        <input type="checkbox"
                               name="event_cancellations"
                               {% if form.instance.event_cancellations %}checked{% endif %}
                               class="toggle toggle-primary toggle-sm">
                    </label>
                </div>
            </div>
        </div>

        <!-- Częstotliwość -->
        <div class="card bg-base-100 shadow mb-6">
            <div class="card-body">
                <h2 class="card-title">Częstotliwość</h2>

                <div class="form-control">
                    <label class="label">
                        <span class="label-text">Tryb powiadomień</span>
                    </label>
                    <select name="digest_frequency" class="select select-bordered w-full">
                        <option value="INSTANT" {% if form.instance.digest_frequency == 'INSTANT' %}selected{% endif %}>
                            Natychmiastowe
                        </option>
                        <option value="HOURLY" {% if form.instance.digest_frequency == 'HOURLY' %}selected{% endif %}>
                            Co godzinę (podsumowanie)
                        </option>
                        <option value="DAILY" {% if form.instance.digest_frequency == 'DAILY' %}selected{% endif %}>
                            Raz dziennie
                        </option>
                        <option value="WEEKLY" {% if form.instance.digest_frequency == 'WEEKLY' %}selected{% endif %}>
                            Raz w tygodniu
                        </option>
                    </select>
                </div>

                <div class="grid grid-cols-2 gap-4 mt-4">
                    <div class="form-control">
                        <label class="label">
                            <span class="label-text">Cisza od (godzina)</span>
                        </label>
                        <select name="quiet_hours_start" class="select select-bordered w-full">
                            <option value="">Wyłączone</option>
                            {% for i in "0123456789101112131415161718192021222324"|make_list %}
                            <option value="{{ forloop.counter0 }}">{{ forloop.counter0|stringformat:"02d" }}:00</option>
                            {% endfor %}
                        </select>
                    </div>

                    <div class="form-control">
                        <label class="label">
                            <span class="label-text">Cisza do (godzina)</span>
                        </label>
                        <select name="quiet_hours_end" class="select select-bordered w-full">
                            <option value="">Wyłączone</option>
                            {% for i in "0123456789101112131415161718192021222324"|make_list %}
                            <option value="{{ forloop.counter0 }}">{{ forloop.counter0|stringformat:"02d" }}:00</option>
                            {% endfor %}
                        </select>
                    </div>
                </div>
            </div>
        </div>

        <div class="flex justify-end">
            <button type="submit" class="btn btn-primary">
                Zapisz ustawienia
            </button>
        </div>
    </form>
</div>
{% endblock %}
```

---

## EMAIL TEMPLATES

### Notification Email Template

**File**: `templates/notifications/email/notification.html`

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f6f9fc; margin: 0; padding: 0;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f6f9fc;">
        <tr>
            <td align="center" style="padding: 40px 0;">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="padding: 32px 32px 20px; text-align: center; border-bottom: 1px solid #e5e7eb;">
                            <h1 style="font-size: 24px; font-weight: bold; color: #3B82F6; margin: 0;">Na Piątkę</h1>
                        </td>
                    </tr>

                    <!-- Content -->
                    <tr>
                        <td style="padding: 32px;">
                            <h2 style="font-size: 20px; font-weight: bold; margin: 0 0 16px;">
                                {{ notification.title }}
                            </h2>

                            <p style="font-size: 16px; line-height: 24px; color: #525252; margin: 0 0 24px;">
                                {{ notification.message }}
                            </p>

                            {% if notification.action_url %}
                            <a href="{{ site_url }}{{ notification.action_url }}"
                               style="display: inline-block; background-color: #3B82F6; color: #ffffff; text-decoration: none; padding: 12px 24px; border-radius: 8px; font-weight: 500;">
                                {{ notification.action_label|default:"Zobacz szczegóły" }}
                            </a>
                            {% endif %}
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="padding: 24px 32px; border-top: 1px solid #e5e7eb; text-align: center;">
                            <p style="font-size: 12px; color: #8898aa; margin: 0;">
                                © 2025 Na Piątkę. Wszystkie prawa zastrzeżone.
                            </p>
                            <p style="font-size: 12px; color: #8898aa; margin: 8px 0 0;">
                                <a href="{{ site_url }}{% url 'notifications:preferences' %}"
                                   style="color: #3B82F6;">
                                    Zarządzaj ustawieniami powiadomień
                                </a>
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
```

---

## URL CONFIGURATION

**File**: `apps/notifications/urls.py`

```python
from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    # User notifications
    path('', views.NotificationListView.as_view(), name='list'),
    path('dropdown/', views.NotificationDropdownView.as_view(), name='dropdown'),
    path('count/', views.UnreadCountView.as_view(), name='unread_count'),
    path('preferences/', views.NotificationPreferencesView.as_view(), name='preferences'),

    # Actions
    path('<uuid:notification_id>/read/', views.MarkAsReadView.as_view(), name='mark_read'),
    path('mark-all-read/', views.MarkAllAsReadView.as_view(), name='mark_all_read'),
    path('<uuid:notification_id>/archive/', views.ArchiveNotificationView.as_view(), name='archive'),
    path('<uuid:notification_id>/delete/', views.DeleteNotificationView.as_view(), name='delete'),

    # Announcements
    path('announcements/', views.AnnouncementListView.as_view(), name='announcement_list'),
    path('announcements/banner/', views.AnnouncementBannerView.as_view(), name='announcement_banner'),
    path('announcements/create/', views.CreateAnnouncementView.as_view(), name='announcement_create'),
    path('announcements/<uuid:announcement_id>/delete/', views.DeleteAnnouncementView.as_view(), name='announcement_delete'),
]
```

---

## HTMX POLLING SETUP

### Base Template Integration

**File**: `templates/base.html` (fragment)

```html
<!-- W nagłówku dodaj HTMX polling dla powiadomień -->
<div hx-get="{% url 'notifications:dropdown' %}"
     hx-trigger="load, every 30s"
     hx-target="this"
     hx-swap="innerHTML">
    <!-- Notification dropdown będzie załadowany tutaj -->
</div>

<!-- Banner ogłoszeń pod nagłówkiem -->
<div id="announcements"
     hx-get="{% url 'notifications:announcement_banner' %}"
     hx-trigger="load"
     hx-swap="innerHTML">
</div>
```

---

## COMPLETION CHECKLIST

- [ ] Notification model with types and priorities
- [ ] NotificationPreference model
- [ ] Announcement model with targeting
- [ ] NotificationService with all operations
- [ ] Celery tasks for email sending
- [ ] Digest emails (hourly, daily, weekly)
- [ ] Notification preferences UI
- [ ] Announcement management (admin)
- [ ] HTMX polling for real-time updates
- [ ] Email templates (notification, digest)
- [ ] Quiet hours support
- [ ] Notification cleanup task

---

**Next Phase**: 9 - User Portals (Tutor, Student, Parent)
