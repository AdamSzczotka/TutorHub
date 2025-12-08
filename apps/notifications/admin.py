from django.contrib import admin

from .models import Announcement, Notification

# NotificationPreference admin is in apps.accounts.admin


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'user',
        'type',
        'priority',
        'is_read',
        'is_archived',
        'created_at',
    ]
    list_filter = ['type', 'priority', 'is_read', 'is_archived', 'created_at']
    search_fields = ['user__email', 'title', 'message']
    raw_id_fields = ['user']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'read_at', 'archived_at']


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'type',
        'is_pinned',
        'publish_at',
        'expires_at',
        'created_by',
    ]
    list_filter = ['type', 'is_pinned', 'created_at']
    search_fields = ['title', 'content']
    raw_id_fields = ['created_by']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'updated_at']
