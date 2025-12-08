from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.views import View
from django.views.generic import ListView, TemplateView

from apps.accounts.models import NotificationPreference
from apps.core.mixins import AdminRequiredMixin, HTMXMixin

from .forms import AnnouncementForm, NotificationPreferenceForm
from .models import Announcement
from .services import AnnouncementService, NotificationService


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
            limit=100,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['unread_count'] = NotificationService.get_unread_count(self.request.user)
        return context


class NotificationDropdownView(LoginRequiredMixin, View):
    """Dropdown z powiadomieniami (dla nagłówka)."""

    def get(self, request):
        notifications = NotificationService.get_user_notifications(
            request.user,
            include_read=False,
            limit=10,
        )
        unread_count = NotificationService.get_unread_count(request.user)

        html = render_to_string(
            'notifications/partials/_dropdown.html',
            {
                'notifications': notifications,
                'unread_count': unread_count,
            },
            request=request,
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
                    request=request,
                )
            )

        return JsonResponse({'count': count})


class MarkAsReadView(LoginRequiredMixin, View):
    """Oznacza powiadomienie jako przeczytane."""

    def post(self, request, notification_id):
        NotificationService.mark_as_read(notification_id, request.user)

        return HttpResponse(
            status=204,
            headers={'HX-Trigger': 'notificationRead'},
        )


class MarkAllAsReadView(LoginRequiredMixin, View):
    """Oznacza wszystkie powiadomienia jako przeczytane."""

    def post(self, request):
        NotificationService.mark_all_as_read(request.user)

        return HttpResponse(
            status=204,
            headers={'HX-Trigger': 'allNotificationsRead'},
        )


class ArchiveNotificationView(LoginRequiredMixin, View):
    """Archiwizuje powiadomienie."""

    def post(self, request, notification_id):
        NotificationService.archive_notification(notification_id, request.user)

        return HttpResponse(
            status=204,
            headers={'HX-Trigger': 'notificationArchived'},
        )


class DeleteNotificationView(LoginRequiredMixin, View):
    """Usuwa powiadomienie."""

    def delete(self, request, notification_id):
        NotificationService.delete_notification(notification_id, request.user)

        return HttpResponse(
            status=204,
            headers={'HX-Trigger': 'notificationDeleted'},
        )


class NotificationPreferencesView(LoginRequiredMixin, TemplateView):
    """Ustawienia powiadomień użytkownika."""

    template_name = 'notifications/preferences.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        prefs, _ = NotificationPreference.objects.get_or_create(user=self.request.user)
        context['form'] = NotificationPreferenceForm(instance=prefs)

        return context

    def post(self, request):
        prefs, _ = NotificationPreference.objects.get_or_create(user=request.user)
        form = NotificationPreferenceForm(request.POST, instance=prefs)

        if form.is_valid():
            form.save()

            if request.headers.get('HX-Request'):
                return HttpResponse(
                    status=204,
                    headers={'HX-Trigger': 'preferencesSaved'},
                )

            return redirect('notifications:preferences')

        return self.render_to_response({'form': form})


# ========== ANNOUNCEMENTS ==========


class AnnouncementBannerView(LoginRequiredMixin, View):
    """Wyświetla aktywne ogłoszenia."""

    def get(self, request):
        announcements = AnnouncementService.get_active_announcements(request.user)

        html = render_to_string(
            'notifications/partials/_announcement_banner.html',
            {'announcements': announcements},
            request=request,
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
                request=request,
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
                expires_at=form.cleaned_data.get('expires_at'),
            )

            # Powiadom użytkowników
            if form.cleaned_data.get('notify_users'):
                target_roles = form.cleaned_data.get('target_roles', [])
                if target_roles:
                    NotificationService.notify_by_role(
                        roles=target_roles,
                        title=announcement.title,
                        message=announcement.content[:200],
                        notification_type='ANNOUNCEMENT',
                        action_url='/panel/notifications/',
                        action_label='Zobacz ogłoszenie',
                    )

            return HttpResponse(
                status=204,
                headers={'HX-Trigger': 'announcementCreated'},
            )

        return HttpResponse(
            render_to_string(
                'admin_panel/announcements/partials/_form.html',
                {'form': form},
                request=request,
            ),
            status=400,
        )


class DeleteAnnouncementView(LoginRequiredMixin, AdminRequiredMixin, View):
    """Usuwa ogłoszenie."""

    def delete(self, request, announcement_id):
        AnnouncementService.delete_announcement(announcement_id)

        return HttpResponse(
            status=204,
            headers={'HX-Trigger': 'announcementDeleted'},
        )
