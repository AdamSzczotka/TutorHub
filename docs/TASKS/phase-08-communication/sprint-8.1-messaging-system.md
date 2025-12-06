# Phase 8 - Sprint 8.1: Messaging System (Django)

## Tasks 098-102: Internal Messaging Platform

> **Duration**: Week 12 (Days 1-3)
> **Goal**: Complete internal messaging system with rich text, threads, attachments, and search
> **Dependencies**: Phase 1-7 completed

---

## SPRINT OVERVIEW

| Task ID | Description                       | Priority | Dependencies     |
| ------- | --------------------------------- | -------- | ---------------- |
| 098     | Message models and database       | Critical | Phase 7 complete |
| 099     | Message composer with rich text   | Critical | Task 098         |
| 100     | Conversation threads              | Critical | Task 099         |
| 101     | Attachment handling               | High     | Task 100         |
| 102     | Message search with filtering     | High     | Task 101         |

---

## MESSAGE MODELS

### Conversation and Message Models

**File**: `apps/messages/models.py`

```python
import uuid
from django.db import models
from django.conf import settings


class MessageContentType(models.TextChoices):
    TEXT = 'TEXT', 'Tekst'
    RICH_TEXT = 'RICH_TEXT', 'Tekst sformatowany'
    CODE = 'CODE', 'Kod'
    SYSTEM = 'SYSTEM', 'Systemowa'


class Conversation(models.Model):
    """Model konwersacji (wątku wiadomości)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subject = models.CharField('Temat', max_length=200, blank=True)
    is_group_chat = models.BooleanField('Czat grupowy', default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_message_at = models.DateTimeField('Ostatnia wiadomość', auto_now_add=True)

    class Meta:
        db_table = 'conversations'
        verbose_name = 'Konwersacja'
        verbose_name_plural = 'Konwersacje'
        ordering = ['-last_message_at']

    def __str__(self):
        return self.subject or f"Konwersacja {self.id}"


class ConversationParticipant(models.Model):
    """Uczestnik konwersacji."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='participants'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='conversation_participations'
    )

    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)
    last_read_at = models.DateTimeField(null=True, blank=True)
    is_archived = models.BooleanField(default=False)
    is_muted = models.BooleanField(default=False)

    class Meta:
        db_table = 'conversation_participants'
        verbose_name = 'Uczestnik konwersacji'
        verbose_name_plural = 'Uczestnicy konwersacji'
        unique_together = ['conversation', 'user']
        indexes = [
            models.Index(fields=['user', 'conversation']),
            models.Index(fields=['last_read_at']),
        ]


class Message(models.Model):
    """Model wiadomości."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )

    # Content
    content = models.TextField('Treść')
    content_type = models.CharField(
        'Typ treści',
        max_length=20,
        choices=MessageContentType.choices,
        default=MessageContentType.TEXT
    )

    # Metadata
    is_edited = models.BooleanField('Edytowana', default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField('Usunięta', default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    # Threading
    reply_to = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='replies'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'messages'
        verbose_name = 'Wiadomość'
        verbose_name_plural = 'Wiadomości'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', '-created_at']),
            models.Index(fields=['sender']),
        ]

    def __str__(self):
        return f"Wiadomość od {self.sender} - {self.created_at}"


class MessageAttachment(models.Model):
    """Załącznik do wiadomości."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='attachments'
    )

    file_name = models.CharField('Nazwa pliku', max_length=255)
    file = models.FileField('Plik', upload_to='message_attachments/%Y/%m/')
    file_size = models.PositiveIntegerField('Rozmiar (bytes)')
    mime_type = models.CharField('Typ MIME', max_length=100)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'message_attachments'
        verbose_name = 'Załącznik'
        verbose_name_plural = 'Załączniki'

    def __str__(self):
        return self.file_name


class MessageReadReceipt(models.Model):
    """Potwierdzenie przeczytania wiadomości."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='read_receipts'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='message_read_receipts'
    )
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'message_read_receipts'
        verbose_name = 'Potwierdzenie odczytu'
        verbose_name_plural = 'Potwierdzenia odczytu'
        unique_together = ['message', 'user']
        indexes = [
            models.Index(fields=['user']),
        ]
```

---

## MESSAGING SERVICE

### Core Messaging Service

**File**: `apps/messages/services.py`

```python
from django.db import transaction
from django.utils import timezone
from django.db.models import Q, Count, Max, Prefetch
from django.contrib.postgres.search import SearchVector, SearchQuery

from .models import (
    Conversation, ConversationParticipant, Message,
    MessageAttachment, MessageReadReceipt
)


class MessagingService:
    """Serwis do obsługi wiadomości."""

    @classmethod
    @transaction.atomic
    def create_conversation(
        cls,
        creator,
        participant_ids: list,
        subject: str = '',
        is_group_chat: bool = False,
        initial_message: str = None
    ):
        """Tworzy nową konwersację."""

        # Dla konwersacji 1-1 sprawdź czy już istnieje
        if not is_group_chat and len(participant_ids) == 1:
            existing = cls._find_existing_direct_conversation(
                creator.id, participant_ids[0]
            )
            if existing:
                return existing, False  # existing, is_new

        conversation = Conversation.objects.create(
            subject=subject,
            is_group_chat=is_group_chat
        )

        # Dodaj twórcę jako uczestnika
        ConversationParticipant.objects.create(
            conversation=conversation,
            user=creator
        )

        # Dodaj pozostałych uczestników
        for user_id in participant_ids:
            if str(user_id) != str(creator.id):
                ConversationParticipant.objects.create(
                    conversation=conversation,
                    user_id=user_id
                )

        # Wyślij początkową wiadomość
        if initial_message:
            cls.send_message(
                conversation=conversation,
                sender=creator,
                content=initial_message
            )

        return conversation, True

    @classmethod
    def _find_existing_direct_conversation(cls, user1_id, user2_id):
        """Znajduje istniejącą konwersację 1-1."""

        conversations = Conversation.objects.filter(
            is_group_chat=False,
            participants__user_id=user1_id
        ).filter(
            participants__user_id=user2_id
        ).annotate(
            participant_count=Count('participants')
        ).filter(
            participant_count=2
        ).first()

        return conversations

    @classmethod
    @transaction.atomic
    def send_message(
        cls,
        conversation,
        sender,
        content: str,
        content_type: str = 'TEXT',
        reply_to_id: str = None,
        attachments: list = None
    ):
        """Wysyła wiadomość w konwersacji."""

        # Sprawdź czy nadawca jest uczestnikiem
        if not ConversationParticipant.objects.filter(
            conversation=conversation,
            user=sender,
            left_at__isnull=True
        ).exists():
            raise ValueError("Nie jesteś uczestnikiem tej konwersacji")

        message = Message.objects.create(
            conversation=conversation,
            sender=sender,
            content=content,
            content_type=content_type,
            reply_to_id=reply_to_id
        )

        # Dodaj załączniki
        if attachments:
            for attachment_data in attachments:
                MessageAttachment.objects.create(
                    message=message,
                    file_name=attachment_data['file_name'],
                    file=attachment_data['file'],
                    file_size=attachment_data['file_size'],
                    mime_type=attachment_data['mime_type']
                )

        # Aktualizuj czas ostatniej wiadomości
        conversation.last_message_at = timezone.now()
        conversation.save(update_fields=['last_message_at'])

        # Automatycznie oznacz jako przeczytane dla nadawcy
        MessageReadReceipt.objects.create(
            message=message,
            user=sender
        )

        return message

    @classmethod
    def get_user_conversations(cls, user, include_archived=False):
        """Pobiera konwersacje użytkownika."""

        queryset = Conversation.objects.filter(
            participants__user=user,
            participants__left_at__isnull=True
        )

        if not include_archived:
            queryset = queryset.filter(participants__is_archived=False)

        # Prefetch dla optymalizacji
        queryset = queryset.prefetch_related(
            Prefetch(
                'participants',
                queryset=ConversationParticipant.objects.select_related('user')
            ),
            Prefetch(
                'messages',
                queryset=Message.objects.filter(is_deleted=False)
                    .order_by('-created_at')[:1]
            )
        ).annotate(
            unread_count=Count(
                'messages',
                filter=Q(messages__is_deleted=False) & ~Q(
                    messages__read_receipts__user=user
                )
            )
        ).order_by('-last_message_at')

        return queryset

    @classmethod
    def get_conversation_messages(cls, conversation_id, user, limit=50, offset=0):
        """Pobiera wiadomości z konwersacji."""

        # Sprawdź uprawnienia
        if not ConversationParticipant.objects.filter(
            conversation_id=conversation_id,
            user=user,
            left_at__isnull=True
        ).exists():
            raise PermissionError("Brak dostępu do konwersacji")

        messages = Message.objects.filter(
            conversation_id=conversation_id,
            is_deleted=False
        ).select_related(
            'sender',
            'reply_to',
            'reply_to__sender'
        ).prefetch_related(
            'attachments',
            'read_receipts'
        ).order_by('-created_at')[offset:offset + limit]

        return list(reversed(messages))

    @classmethod
    def mark_as_read(cls, message_ids: list, user):
        """Oznacza wiadomości jako przeczytane."""

        receipts = []
        for message_id in message_ids:
            receipt, created = MessageReadReceipt.objects.get_or_create(
                message_id=message_id,
                user=user
            )
            if created:
                receipts.append(receipt)

        # Aktualizuj last_read_at uczestnika
        Message.objects.filter(id__in=message_ids).values(
            'conversation_id'
        ).distinct()

        conversations = Message.objects.filter(
            id__in=message_ids
        ).values_list('conversation_id', flat=True).distinct()

        ConversationParticipant.objects.filter(
            conversation_id__in=conversations,
            user=user
        ).update(last_read_at=timezone.now())

        return len(receipts)

    @classmethod
    def edit_message(cls, message_id, user, new_content: str):
        """Edytuje wiadomość."""

        message = Message.objects.get(id=message_id)

        if message.sender != user:
            raise PermissionError("Możesz edytować tylko własne wiadomości")

        message.content = new_content
        message.is_edited = True
        message.edited_at = timezone.now()
        message.save()

        return message

    @classmethod
    def delete_message(cls, message_id, user):
        """Usuwa wiadomość (soft delete)."""

        message = Message.objects.get(id=message_id)

        if message.sender != user:
            raise PermissionError("Możesz usunąć tylko własne wiadomości")

        message.is_deleted = True
        message.deleted_at = timezone.now()
        message.save()

        return True

    @classmethod
    def search_messages(
        cls,
        user,
        query: str,
        conversation_id: str = None,
        sender_id: str = None,
        start_date=None,
        end_date=None,
        limit=20,
        offset=0
    ):
        """Wyszukuje wiadomości."""

        # Bazowy queryset - tylko konwersacje użytkownika
        user_conversations = ConversationParticipant.objects.filter(
            user=user,
            left_at__isnull=True
        ).values_list('conversation_id', flat=True)

        queryset = Message.objects.filter(
            conversation_id__in=user_conversations,
            is_deleted=False,
            content__icontains=query
        )

        if conversation_id:
            queryset = queryset.filter(conversation_id=conversation_id)

        if sender_id:
            queryset = queryset.filter(sender_id=sender_id)

        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)

        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)

        total_count = queryset.count()
        messages = queryset.select_related(
            'sender', 'conversation'
        ).prefetch_related('attachments')[offset:offset + limit]

        return {
            'messages': messages,
            'total_count': total_count,
            'has_more': offset + limit < total_count
        }

    @classmethod
    def archive_conversation(cls, conversation_id, user):
        """Archiwizuje konwersację dla użytkownika."""

        ConversationParticipant.objects.filter(
            conversation_id=conversation_id,
            user=user
        ).update(is_archived=True)

    @classmethod
    def mute_conversation(cls, conversation_id, user, mute=True):
        """Wycisza/odcisza konwersację."""

        ConversationParticipant.objects.filter(
            conversation_id=conversation_id,
            user=user
        ).update(is_muted=mute)
```

---

## MESSAGING VIEWS

### Conversation Views

**File**: `apps/messages/views.py`

```python
from django.views.generic import ListView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils import timezone

from apps.core.mixins import HTMXMixin
from .models import Conversation, Message, ConversationParticipant
from .services import MessagingService
from .forms import MessageForm, ConversationForm


class ConversationListView(LoginRequiredMixin, HTMXMixin, ListView):
    """Lista konwersacji użytkownika."""

    template_name = 'messages/conversation_list.html'
    partial_template_name = 'messages/partials/_conversation_list.html'
    context_object_name = 'conversations'

    def get_queryset(self):
        include_archived = self.request.GET.get('archived') == 'true'
        return MessagingService.get_user_conversations(
            self.request.user,
            include_archived=include_archived
        )


class ConversationDetailView(LoginRequiredMixin, HTMXMixin, DetailView):
    """Widok pojedynczej konwersacji."""

    model = Conversation
    template_name = 'messages/conversation_detail.html'
    partial_template_name = 'messages/partials/_message_thread.html'
    context_object_name = 'conversation'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['messages'] = MessagingService.get_conversation_messages(
            self.object.id,
            self.request.user
        )
        context['form'] = MessageForm()
        return context

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)

        # Oznacz wiadomości jako przeczytane
        unread_messages = Message.objects.filter(
            conversation=self.object,
            is_deleted=False
        ).exclude(
            sender=request.user
        ).exclude(
            read_receipts__user=request.user
        ).values_list('id', flat=True)

        if unread_messages:
            MessagingService.mark_as_read(list(unread_messages), request.user)

        return response


class CreateConversationView(LoginRequiredMixin, View):
    """Tworzy nową konwersację."""

    def get(self, request):
        """Wyświetla formularz tworzenia konwersacji."""
        form = ConversationForm()
        return HttpResponse(
            render_to_string(
                'messages/partials/_conversation_form.html',
                {'form': form},
                request=request
            )
        )

    def post(self, request):
        """Obsługuje tworzenie konwersacji."""
        form = ConversationForm(request.POST)

        if form.is_valid():
            participant_ids = form.cleaned_data['participants']
            subject = form.cleaned_data.get('subject', '')
            initial_message = form.cleaned_data.get('initial_message', '')
            is_group = len(participant_ids) > 1

            conversation, is_new = MessagingService.create_conversation(
                creator=request.user,
                participant_ids=participant_ids,
                subject=subject,
                is_group_chat=is_group,
                initial_message=initial_message
            )

            return HttpResponse(
                status=204,
                headers={
                    'HX-Redirect': f'/messages/{conversation.id}/'
                }
            )

        return HttpResponse(
            render_to_string(
                'messages/partials/_conversation_form.html',
                {'form': form},
                request=request
            ),
            status=400
        )


class SendMessageView(LoginRequiredMixin, View):
    """Wysyła wiadomość w konwersacji."""

    def post(self, request, conversation_id):
        conversation = get_object_or_404(Conversation, id=conversation_id)
        form = MessageForm(request.POST, request.FILES)

        if form.is_valid():
            attachments = []
            for file in request.FILES.getlist('attachments'):
                attachments.append({
                    'file_name': file.name,
                    'file': file,
                    'file_size': file.size,
                    'mime_type': file.content_type
                })

            message = MessagingService.send_message(
                conversation=conversation,
                sender=request.user,
                content=form.cleaned_data['content'],
                content_type=form.cleaned_data.get('content_type', 'TEXT'),
                reply_to_id=form.cleaned_data.get('reply_to'),
                attachments=attachments if attachments else None
            )

            # Zwróć nową wiadomość jako HTML
            html = render_to_string(
                'messages/partials/_message_bubble.html',
                {'message': message, 'current_user': request.user},
                request=request
            )

            return HttpResponse(
                html,
                headers={'HX-Trigger': 'messageSent'}
            )

        return HttpResponse(
            render_to_string(
                'messages/partials/_message_form.html',
                {'form': form, 'conversation': conversation},
                request=request
            ),
            status=400
        )


class EditMessageView(LoginRequiredMixin, View):
    """Edytuje wiadomość."""

    def post(self, request, message_id):
        content = request.POST.get('content')

        try:
            message = MessagingService.edit_message(
                message_id=message_id,
                user=request.user,
                new_content=content
            )

            html = render_to_string(
                'messages/partials/_message_bubble.html',
                {'message': message, 'current_user': request.user},
                request=request
            )

            return HttpResponse(html)
        except PermissionError as e:
            return HttpResponse(str(e), status=403)


class DeleteMessageView(LoginRequiredMixin, View):
    """Usuwa wiadomość."""

    def delete(self, request, message_id):
        try:
            MessagingService.delete_message(
                message_id=message_id,
                user=request.user
            )

            return HttpResponse(
                status=204,
                headers={'HX-Trigger': 'messageDeleted'}
            )
        except PermissionError as e:
            return HttpResponse(str(e), status=403)


class MarkAsReadView(LoginRequiredMixin, View):
    """Oznacza wiadomości jako przeczytane."""

    def post(self, request):
        import json
        data = json.loads(request.body)
        message_ids = data.get('message_ids', [])

        count = MessagingService.mark_as_read(message_ids, request.user)

        return JsonResponse({'marked': count})


class SearchMessagesView(LoginRequiredMixin, HTMXMixin, View):
    """Wyszukuje wiadomości."""

    def get(self, request):
        query = request.GET.get('q', '').strip()
        conversation_id = request.GET.get('conversation_id')
        sender_id = request.GET.get('sender_id')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        if len(query) < 2:
            return HttpResponse('')

        results = MessagingService.search_messages(
            user=request.user,
            query=query,
            conversation_id=conversation_id,
            sender_id=sender_id,
            start_date=start_date,
            end_date=end_date
        )

        return HttpResponse(
            render_to_string(
                'messages/partials/_search_results.html',
                {
                    'results': results,
                    'query': query
                },
                request=request
            )
        )


class ArchiveConversationView(LoginRequiredMixin, View):
    """Archiwizuje konwersację."""

    def post(self, request, conversation_id):
        MessagingService.archive_conversation(conversation_id, request.user)
        return HttpResponse(
            status=204,
            headers={'HX-Trigger': 'conversationArchived'}
        )


class MuteConversationView(LoginRequiredMixin, View):
    """Wycisza konwersację."""

    def post(self, request, conversation_id):
        mute = request.POST.get('mute', 'true') == 'true'
        MessagingService.mute_conversation(conversation_id, request.user, mute)
        return HttpResponse(
            status=204,
            headers={'HX-Trigger': 'conversationMuted'}
        )
```

---

## MESSAGE FORMS

**File**: `apps/messages/forms.py`

```python
from django import forms
from django.contrib.auth import get_user_model

from .models import Message, MessageContentType

User = get_user_model()


class ConversationForm(forms.Form):
    """Formularz tworzenia konwersacji."""

    participants = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True),
        widget=forms.SelectMultiple(attrs={
            'class': 'select select-bordered w-full',
            'x-data': '',
            'x-init': "new TomSelect($el)"
        }),
        label='Uczestnicy',
        help_text='Wybierz uczestników konwersacji'
    )
    subject = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'Temat konwersacji (opcjonalnie)'
        }),
        label='Temat'
    )
    initial_message = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'textarea textarea-bordered w-full',
            'rows': 3,
            'placeholder': 'Pierwsza wiadomość (opcjonalnie)'
        }),
        label='Wiadomość początkowa'
    )


class MessageForm(forms.Form):
    """Formularz wysyłania wiadomości."""

    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'textarea textarea-bordered w-full',
            'rows': 3,
            'placeholder': 'Wpisz wiadomość...',
            'x-model': 'content',
            'x-on:keydown.ctrl.enter': '$refs.submitBtn.click()'
        }),
        label='Treść'
    )
    content_type = forms.ChoiceField(
        choices=MessageContentType.choices,
        initial=MessageContentType.TEXT,
        required=False,
        widget=forms.HiddenInput()
    )
    reply_to = forms.UUIDField(
        required=False,
        widget=forms.HiddenInput()
    )
    attachments = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={
            'class': 'file-input file-input-bordered w-full',
            'multiple': True,
            'accept': 'image/*,.pdf,.doc,.docx,.xls,.xlsx'
        }),
        label='Załączniki'
    )

    def clean_attachments(self):
        files = self.files.getlist('attachments')

        if len(files) > 5:
            raise forms.ValidationError('Maksymalnie 5 załączników')

        for file in files:
            if file.size > 10 * 1024 * 1024:  # 10MB
                raise forms.ValidationError(
                    f'Plik {file.name} przekracza limit 10MB'
                )

        return files
```

---

## MESSAGE TEMPLATES

### Conversation List Template

**File**: `templates/messages/conversation_list.html`

```html
{% extends "base.html" %}

{% block content %}
<div class="max-w-4xl mx-auto p-6">
    <div class="flex items-center justify-between mb-6">
        <h1 class="text-2xl font-bold">Wiadomości</h1>
        <button class="btn btn-primary"
                hx-get="{% url 'messages:create' %}"
                hx-target="#modal-content"
                hx-swap="innerHTML"
                onclick="document.getElementById('modal').showModal()">
            + Nowa konwersacja
        </button>
    </div>

    <!-- Search -->
    <div class="mb-4">
        <input type="text"
               class="input input-bordered w-full"
               placeholder="Szukaj wiadomości..."
               hx-get="{% url 'messages:search' %}"
               hx-trigger="input changed delay:300ms"
               hx-target="#search-results"
               name="q">
        <div id="search-results" class="mt-2"></div>
    </div>

    <!-- Tabs -->
    <div class="tabs tabs-boxed mb-4">
        <a class="tab tab-active"
           hx-get="{% url 'messages:list' %}"
           hx-target="#conversation-list"
           hx-push-url="true">
            Aktywne
        </a>
        <a class="tab"
           hx-get="{% url 'messages:list' %}?archived=true"
           hx-target="#conversation-list"
           hx-push-url="true">
            Archiwum
        </a>
    </div>

    <!-- Conversation List -->
    <div id="conversation-list"
         hx-get="{% url 'messages:list' %}"
         hx-trigger="conversationArchived from:body, messageSent from:body">
        {% include "messages/partials/_conversation_list.html" %}
    </div>
</div>

<!-- Modal -->
<dialog id="modal" class="modal">
    <div class="modal-box max-w-xl">
        <div id="modal-content"></div>
    </div>
    <form method="dialog" class="modal-backdrop">
        <button>close</button>
    </form>
</dialog>
{% endblock %}
```

### Conversation List Partial

**File**: `templates/messages/partials/_conversation_list.html`

```html
{% if conversations %}
<div class="divide-y rounded-lg border bg-white">
    {% for conversation in conversations %}
    <a href="{% url 'messages:detail' conversation.id %}"
       class="flex items-start p-4 hover:bg-gray-50 transition-colors {% if conversation.unread_count > 0 %}bg-blue-50{% endif %}">

        <!-- Avatar(s) -->
        <div class="flex -space-x-2 mr-3">
            {% for participant in conversation.participants.all|slice:":3" %}
            {% if participant.user != request.user %}
            <div class="avatar">
                <div class="w-10 rounded-full ring-2 ring-white">
                    {% if participant.user.avatar %}
                    <img src="{{ participant.user.avatar.url }}" alt="">
                    {% else %}
                    <div class="bg-primary text-white flex items-center justify-center text-sm font-bold w-full h-full">
                        {{ participant.user.first_name.0 }}{{ participant.user.last_name.0 }}
                    </div>
                    {% endif %}
                </div>
            </div>
            {% endif %}
            {% endfor %}
        </div>

        <!-- Content -->
        <div class="flex-1 min-w-0">
            <div class="flex items-center justify-between mb-1">
                <h3 class="font-medium truncate">
                    {% if conversation.subject %}
                        {{ conversation.subject }}
                    {% else %}
                        {% for p in conversation.participants.all %}
                            {% if p.user != request.user %}
                                {{ p.user.get_full_name }}{% if not forloop.last %}, {% endif %}
                            {% endif %}
                        {% endfor %}
                    {% endif %}
                </h3>
                <span class="text-xs text-gray-500">
                    {{ conversation.last_message_at|timesince }} temu
                </span>
            </div>

            {% with last_message=conversation.messages.first %}
            {% if last_message %}
            <p class="text-sm text-gray-600 truncate">
                {% if last_message.sender == request.user %}Ty: {% endif %}
                {{ last_message.content|striptags|truncatewords:10 }}
            </p>
            {% endif %}
            {% endwith %}

            {% if conversation.unread_count > 0 %}
            <span class="badge badge-primary badge-sm mt-1">
                {{ conversation.unread_count }} nowe
            </span>
            {% endif %}
        </div>
    </a>
    {% endfor %}
</div>
{% else %}
<div class="text-center py-12 text-gray-500">
    <svg class="mx-auto h-12 w-12 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"></path>
    </svg>
    <p>Brak konwersacji</p>
    <p class="text-sm mt-2">Rozpocznij nową konwersację!</p>
</div>
{% endif %}
```

### Message Thread Template

**File**: `templates/messages/partials/_message_thread.html`

```html
<div class="flex flex-col h-[calc(100vh-200px)]">
    <!-- Messages -->
    <div id="message-thread"
         class="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50"
         x-data="{ scrollToBottom() { this.$el.scrollTop = this.$el.scrollHeight } }"
         x-init="scrollToBottom()"
         hx-trigger="messageSent from:body"
         hx-get="{% url 'messages:detail' conversation.id %}"
         hx-select="#message-thread"
         hx-swap="outerHTML">

        {% regroup messages by created_at.date as messages_by_date %}
        {% for date_group in messages_by_date %}
        <div class="flex items-center justify-center my-4">
            <span class="bg-white border rounded-full px-3 py-1 text-xs text-gray-600">
                {{ date_group.grouper|date:"d F Y" }}
            </span>
        </div>

        {% for message in date_group.list %}
        {% include "messages/partials/_message_bubble.html" with message=message current_user=request.user %}
        {% endfor %}
        {% endfor %}
    </div>

    <!-- Composer -->
    <div class="border-t bg-white p-4"
         x-data="{ content: '', replyTo: null }">

        <!-- Reply indicator -->
        <template x-if="replyTo">
            <div class="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-3 flex items-start justify-between">
                <div>
                    <div class="text-xs font-medium text-blue-700">
                        Odpowiedź do <span x-text="replyTo.senderName"></span>
                    </div>
                    <div class="text-sm text-gray-600 mt-1 line-clamp-2" x-text="replyTo.content"></div>
                </div>
                <button type="button"
                        class="btn btn-ghost btn-xs"
                        @click="replyTo = null">
                    &times;
                </button>
            </div>
        </template>

        <form hx-post="{% url 'messages:send' conversation.id %}"
              hx-target="#message-thread"
              hx-swap="beforeend"
              hx-on::after-request="this.reset(); Alpine.$data(this).content = ''"
              enctype="multipart/form-data"
              class="space-y-3">
            {% csrf_token %}

            <textarea name="content"
                      x-model="content"
                      class="textarea textarea-bordered w-full"
                      rows="3"
                      placeholder="Wpisz wiadomość..."
                      @keydown.ctrl.enter="$refs.submitBtn.click()"></textarea>

            <input type="hidden" name="reply_to" :value="replyTo?.id">

            <div class="flex items-center justify-between">
                <div>
                    <input type="file"
                           name="attachments"
                           id="file-upload"
                           multiple
                           accept="image/*,.pdf,.doc,.docx,.xls,.xlsx"
                           class="hidden">
                    <label for="file-upload" class="btn btn-outline btn-sm">
                        <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"></path>
                        </svg>
                        Załącz
                    </label>
                </div>

                <button type="submit"
                        x-ref="submitBtn"
                        class="btn btn-primary"
                        :disabled="!content.trim()">
                    <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"></path>
                    </svg>
                    Wyślij
                </button>
            </div>
        </form>
    </div>
</div>
```

### Message Bubble Template

**File**: `templates/messages/partials/_message_bubble.html`

```html
{% load humanize %}

<div class="flex items-start space-x-2 group {% if message.sender == current_user %}flex-row-reverse space-x-reverse{% endif %}"
     id="message-{{ message.id }}">

    <!-- Avatar -->
    <div class="avatar">
        <div class="w-8 rounded-full">
            {% if message.sender.avatar %}
            <img src="{{ message.sender.avatar.url }}" alt="">
            {% else %}
            <div class="bg-gray-300 text-gray-600 flex items-center justify-center text-xs font-bold w-full h-full">
                {{ message.sender.first_name.0 }}{{ message.sender.last_name.0 }}
            </div>
            {% endif %}
        </div>
    </div>

    <!-- Message content -->
    <div class="flex-1 max-w-[70%] space-y-1 {% if message.sender == current_user %}flex flex-col items-end{% endif %}">
        <div class="rounded-lg px-4 py-2 {% if message.sender == current_user %}bg-blue-500 text-white{% else %}bg-gray-100 text-gray-900{% endif %}">

            {% if message.sender != current_user %}
            <div class="text-xs font-medium mb-1">
                {{ message.sender.get_full_name }}
            </div>
            {% endif %}

            {% if message.reply_to %}
            <div class="bg-black/10 rounded px-2 py-1 mb-2 text-xs">
                <div class="font-medium">
                    {{ message.reply_to.sender.get_full_name }}
                </div>
                <div class="line-clamp-2 opacity-75">
                    {{ message.reply_to.content|striptags|truncatewords:15 }}
                </div>
            </div>
            {% endif %}

            <div class="prose prose-sm max-w-none {% if message.sender == current_user %}prose-invert{% endif %}">
                {{ message.content|linebreaks }}
            </div>

            {% if message.attachments.exists %}
            <div class="mt-2 space-y-1">
                {% for attachment in message.attachments.all %}
                <a href="{{ attachment.file.url }}"
                   target="_blank"
                   class="block bg-black/10 rounded px-2 py-1 text-xs hover:bg-black/20">
                    {{ attachment.file_name }} ({{ attachment.file_size|filesizeformat }})
                </a>
                {% endfor %}
            </div>
            {% endif %}
        </div>

        <div class="flex items-center space-x-2 text-xs text-gray-500 {% if message.sender == current_user %}flex-row-reverse space-x-reverse{% endif %}">
            <span>{{ message.created_at|time:"H:i" }}</span>
            {% if message.is_edited %}
            <span class="opacity-75">(edytowano)</span>
            {% endif %}
            {% if message.sender == current_user %}
            <span>
                {% if message.read_receipts.count > 1 %}
                <!-- Double check - read -->
                <svg class="w-3 h-3 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path>
                </svg>
                {% else %}
                <!-- Single check - sent -->
                <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path>
                </svg>
                {% endif %}
            </span>
            {% endif %}
        </div>
    </div>

    <!-- Actions dropdown -->
    <div class="dropdown dropdown-end opacity-0 group-hover:opacity-100 transition-opacity">
        <label tabindex="0" class="btn btn-ghost btn-xs">
            <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z"></path>
            </svg>
        </label>
        <ul tabindex="0" class="dropdown-content menu p-2 shadow bg-base-100 rounded-box w-40 z-10">
            <li>
                <button @click="$dispatch('reply', {
                    id: '{{ message.id }}',
                    content: '{{ message.content|truncatewords:10|escapejs }}',
                    senderName: '{{ message.sender.get_full_name|escapejs }}'
                })">
                    Odpowiedz
                </button>
            </li>
            {% if message.sender == current_user %}
            <li>
                <button hx-get="{% url 'messages:edit' message.id %}"
                        hx-target="#message-{{ message.id }}"
                        hx-swap="outerHTML">
                    Edytuj
                </button>
            </li>
            <li>
                <button hx-delete="{% url 'messages:delete' message.id %}"
                        hx-confirm="Czy na pewno chcesz usunąć tę wiadomość?"
                        hx-target="#message-{{ message.id }}"
                        hx-swap="delete"
                        class="text-error">
                    Usuń
                </button>
            </li>
            {% endif %}
        </ul>
    </div>
</div>
```

---

## URL CONFIGURATION

**File**: `apps/messages/urls.py`

```python
from django.urls import path
from . import views

app_name = 'messages'

urlpatterns = [
    path('', views.ConversationListView.as_view(), name='list'),
    path('create/', views.CreateConversationView.as_view(), name='create'),
    path('search/', views.SearchMessagesView.as_view(), name='search'),
    path('<uuid:pk>/', views.ConversationDetailView.as_view(), name='detail'),
    path('<uuid:conversation_id>/send/', views.SendMessageView.as_view(), name='send'),
    path('<uuid:conversation_id>/archive/', views.ArchiveConversationView.as_view(), name='archive'),
    path('<uuid:conversation_id>/mute/', views.MuteConversationView.as_view(), name='mute'),
    path('message/<uuid:message_id>/edit/', views.EditMessageView.as_view(), name='edit'),
    path('message/<uuid:message_id>/delete/', views.DeleteMessageView.as_view(), name='delete'),
    path('mark-read/', views.MarkAsReadView.as_view(), name='mark_read'),
]
```

---

## COMPLETION CHECKLIST

- [ ] Conversation and Message models created
- [ ] MessagingService with all CRUD operations
- [ ] Create conversation with participants
- [ ] Send messages with attachments
- [ ] Reply to messages (threading)
- [ ] Edit and delete messages
- [ ] Mark as read with receipts
- [ ] Full-text search
- [ ] Archive and mute conversations
- [ ] HTMX templates for real-time feel
- [ ] File upload with validation (5 files, 10MB max)

---

**Next Sprint**: 8.2 - Notifications System
