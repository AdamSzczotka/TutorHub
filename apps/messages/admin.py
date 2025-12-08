from django.contrib import admin

from .models import (
    Conversation,
    ConversationParticipant,
    Message,
    MessageAttachment,
    MessageReadReceipt,
)


class ConversationParticipantInline(admin.TabularInline):
    model = ConversationParticipant
    extra = 0
    raw_id_fields = ['user']


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    raw_id_fields = ['sender', 'reply_to']
    readonly_fields = ['created_at']
    fields = ['sender', 'content', 'content_type', 'created_at']


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['id', 'subject', 'is_group_chat', 'last_message_at', 'created_at']
    list_filter = ['is_group_chat', 'created_at']
    search_fields = ['subject']
    date_hierarchy = 'created_at'
    inlines = [ConversationParticipantInline, MessageInline]


@admin.register(ConversationParticipant)
class ConversationParticipantAdmin(admin.ModelAdmin):
    list_display = ['conversation', 'user', 'joined_at', 'is_archived', 'is_muted']
    list_filter = ['is_archived', 'is_muted']
    search_fields = ['user__email', 'conversation__subject']
    raw_id_fields = ['conversation', 'user']


class MessageAttachmentInline(admin.TabularInline):
    model = MessageAttachment
    extra = 0
    readonly_fields = ['uploaded_at']


class MessageReadReceiptInline(admin.TabularInline):
    model = MessageReadReceipt
    extra = 0
    raw_id_fields = ['user']
    readonly_fields = ['read_at']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'conversation', 'sender', 'content_type', 'is_edited', 'is_deleted', 'created_at']
    list_filter = ['content_type', 'is_edited', 'is_deleted', 'created_at']
    search_fields = ['sender__email', 'content']
    raw_id_fields = ['conversation', 'sender', 'reply_to']
    date_hierarchy = 'created_at'
    inlines = [MessageAttachmentInline, MessageReadReceiptInline]


@admin.register(MessageAttachment)
class MessageAttachmentAdmin(admin.ModelAdmin):
    list_display = ['file_name', 'message', 'file_size', 'mime_type', 'uploaded_at']
    list_filter = ['mime_type', 'uploaded_at']
    search_fields = ['file_name']
    raw_id_fields = ['message']


@admin.register(MessageReadReceipt)
class MessageReadReceiptAdmin(admin.ModelAdmin):
    list_display = ['message', 'user', 'read_at']
    list_filter = ['read_at']
    raw_id_fields = ['message', 'user']
