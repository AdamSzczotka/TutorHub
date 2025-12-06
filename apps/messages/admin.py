from django.contrib import admin

from .models import Message


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'recipient', 'subject', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['sender__email', 'recipient__email', 'subject', 'content']
    raw_id_fields = ['sender', 'recipient', 'parent_message']
    date_hierarchy = 'created_at'
