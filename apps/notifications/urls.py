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
    path(
        '<uuid:notification_id>/read/',
        views.MarkAsReadView.as_view(),
        name='mark_read',
    ),
    path('mark-all-read/', views.MarkAllAsReadView.as_view(), name='mark_all_read'),
    path(
        '<uuid:notification_id>/archive/',
        views.ArchiveNotificationView.as_view(),
        name='archive',
    ),
    path(
        '<uuid:notification_id>/delete/',
        views.DeleteNotificationView.as_view(),
        name='delete',
    ),
    # Announcements
    path(
        'announcements/',
        views.AnnouncementListView.as_view(),
        name='announcement_list',
    ),
    path(
        'announcements/banner/',
        views.AnnouncementBannerView.as_view(),
        name='announcement_banner',
    ),
    path(
        'announcements/create/',
        views.CreateAnnouncementView.as_view(),
        name='announcement_create',
    ),
    path(
        'announcements/<uuid:announcement_id>/delete/',
        views.DeleteAnnouncementView.as_view(),
        name='announcement_delete',
    ),
]
