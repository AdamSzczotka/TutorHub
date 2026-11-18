import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils.html import escape
from django.views import View
from django.views.generic import DetailView, ListView

from apps.core.mixins import HTMXMixin

from .forms import ConversationForm, MessageEditForm, MessageForm
from .models import Conversation, Message
from .services import MessagingService


class ConversationListView(LoginRequiredMixin, HTMXMixin, ListView):
    """Lista konwersacji użytkownika."""

    template_name = 'messages/conversation_list.html'
    partial_template_name = 'messages/partials/_conversation_list.html'
    context_object_name = 'conversations'

    def get_queryset(self):
        include_archived = self.request.GET.get('archived') == 'true'
        return MessagingService.get_user_conversations(
            self.request.user,
            include_archived=include_archived,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['show_archived'] = self.request.GET.get('archived') == 'true'
        return context


class ConversationDetailView(LoginRequiredMixin, HTMXMixin, DetailView):
    """Widok pojedynczej konwersacji."""

    model = Conversation
    template_name = 'messages/conversation_detail.html'
    partial_template_name = 'messages/partials/_message_thread.html'
    context_object_name = 'conversation'

    def get_queryset(self):
        # Only conversations the user participates in (404 otherwise).
        return Conversation.objects.filter(
            participants__user=self.request.user,
            participants__left_at__isnull=True,
        ).distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['messages_list'] = MessagingService.get_conversation_messages(
            self.object.id,
            self.request.user,
        )
        context['form'] = MessageForm()
        return context

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)

        # Oznacz wiadomości jako przeczytane
        unread_messages = (
            Message.objects.filter(
                conversation=self.object,
                is_deleted=False,
            )
            .exclude(sender=request.user)
            .exclude(read_receipts__user=request.user)
            .values_list('id', flat=True)
        )

        if unread_messages:
            MessagingService.mark_as_read(list(unread_messages), request.user)

        return response


class CreateConversationView(LoginRequiredMixin, View):
    """Tworzy nową konwersację."""

    def get(self, request):
        """Wyświetla formularz tworzenia konwersacji."""
        form = ConversationForm(user=request.user)
        return HttpResponse(
            render_to_string(
                'messages/partials/_conversation_form.html',
                {'form': form},
                request=request,
            )
        )

    def post(self, request):
        """Obsługuje tworzenie konwersacji."""
        form = ConversationForm(request.POST, user=request.user)

        if form.is_valid():
            participant_ids = [p.id for p in form.cleaned_data['participants']]
            subject = form.cleaned_data.get('subject', '')
            initial_message = form.cleaned_data.get('initial_message', '')

            # Odfiltruj twórcę z listy uczestników przy sprawdzaniu czy to grupa
            other_participants = [
                pid for pid in participant_ids if str(pid) != str(request.user.id)
            ]
            is_group = len(other_participants) > 1

            conversation, is_new = MessagingService.create_conversation(
                creator=request.user,
                participant_ids=participant_ids,
                subject=subject if is_group else '',  # Temat tylko dla grup
                is_group_chat=is_group,
                initial_message=initial_message if initial_message else None,
            )

            return HttpResponse(
                status=204,
                headers={'HX-Redirect': f'/panel/messages/{conversation.id}/'},
            )

        return HttpResponse(
            render_to_string(
                'messages/partials/_conversation_form.html',
                {'form': form},
                request=request,
            ),
            status=400,
        )


ALLOWED_ATTACHMENT_EXTENSIONS = {
    'pdf', 'jpg', 'jpeg', 'png', 'webp', 'doc', 'docx', 'xls', 'xlsx', 'odt', 'txt',
}
MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_ATTACHMENTS = 5


def _validate_attachments(files):
    """Return an error message or None. Blocks HTML/SVG/JS etc. (stored XSS)."""
    if len(files) > MAX_ATTACHMENTS:
        return f'Maksymalnie {MAX_ATTACHMENTS} załączników.'
    for f in files:
        ext = f.name.rsplit('.', 1)[-1].lower() if '.' in f.name else ''
        if ext not in ALLOWED_ATTACHMENT_EXTENSIONS:
            return f'Niedozwolony typ pliku: {escape(f.name)}'
        if f.size > MAX_ATTACHMENT_SIZE:
            return f'Plik {escape(f.name)} jest za duży (max 10 MB).'
    return None


class SendMessageView(LoginRequiredMixin, View):
    """Wysyła wiadomość w konwersacji."""

    def post(self, request, conversation_id):
        conversation = get_object_or_404(
            Conversation.objects.filter(
                participants__user=request.user,
                participants__left_at__isnull=True,
            ).distinct(),
            id=conversation_id,
        )
        form = MessageForm(request.POST, request.FILES)

        files = request.FILES.getlist('attachments')
        attachment_error = _validate_attachments(files)
        if attachment_error:
            return HttpResponse(attachment_error, status=400)

        if form.is_valid():
            attachments = []
            for file in files:
                attachments.append(
                    {
                        'file_name': file.name,
                        'file': file,
                        'file_size': file.size,
                        'mime_type': file.content_type,
                    }
                )

            message = MessagingService.send_message(
                conversation=conversation,
                sender=request.user,
                content=form.cleaned_data['content'],
                # SYSTEM messages are generated by the app only, never by users.
                content_type=(
                    'TEXT'
                    if form.cleaned_data.get('content_type') in (None, '', 'SYSTEM')
                    else form.cleaned_data['content_type']
                ),
                reply_to_id=form.cleaned_data.get('reply_to'),
                attachments=attachments if attachments else None,
            )

            # Zwróć nową wiadomość jako HTML
            html = render_to_string(
                'messages/partials/_message_bubble.html',
                {'message': message, 'current_user': request.user},
                request=request,
            )

            return HttpResponse(html, headers={'HX-Trigger': 'messageSent'})

        return HttpResponse(
            render_to_string(
                'messages/partials/_message_form.html',
                {'form': form, 'conversation': conversation},
                request=request,
            ),
            status=400,
        )


class EditMessageView(LoginRequiredMixin, View):
    """Edytuje wiadomość."""

    def get(self, request, message_id):
        """Wyświetla formularz edycji."""
        message = get_object_or_404(Message, id=message_id)

        if message.sender != request.user:
            return HttpResponse('Brak uprawnień', status=403)

        form = MessageEditForm(initial={'content': message.content})
        return HttpResponse(
            render_to_string(
                'messages/partials/_message_edit_form.html',
                {'form': form, 'message': message},
                request=request,
            )
        )

    def post(self, request, message_id):
        """Obsługuje edycję wiadomości."""
        form = MessageEditForm(request.POST)

        if form.is_valid():
            try:
                message = MessagingService.edit_message(
                    message_id=message_id,
                    user=request.user,
                    new_content=form.cleaned_data['content'],
                )

                html = render_to_string(
                    'messages/partials/_message_bubble.html',
                    {'message': message, 'current_user': request.user},
                    request=request,
                )

                return HttpResponse(html)
            except PermissionError as e:
                return HttpResponse(str(e), status=403)

        return HttpResponse('Błąd walidacji', status=400)


class DeleteMessageView(LoginRequiredMixin, View):
    """Usuwa wiadomość."""

    def delete(self, request, message_id):
        try:
            MessagingService.delete_message(
                message_id=message_id,
                user=request.user,
            )

            return HttpResponse(
                status=200,
                headers={'HX-Trigger': 'messageDeleted'},
            )
        except PermissionError as e:
            return HttpResponse(str(e), status=403)


class MarkAsReadView(LoginRequiredMixin, View):
    """Oznacza wiadomości jako przeczytane."""

    def post(self, request):
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
            end_date=end_date,
        )

        return HttpResponse(
            render_to_string(
                'messages/partials/_search_results.html',
                {
                    'results': results,
                    'query': query,
                },
                request=request,
            )
        )


class ArchiveConversationView(LoginRequiredMixin, View):
    """Archiwizuje konwersację."""

    def post(self, request, conversation_id):
        MessagingService.archive_conversation(conversation_id, request.user)
        return HttpResponse(
            status=204,
            headers={'HX-Trigger': 'conversationArchived'},
        )


class UnarchiveConversationView(LoginRequiredMixin, View):
    """Przywraca konwersację z archiwum."""

    def post(self, request, conversation_id):
        MessagingService.unarchive_conversation(conversation_id, request.user)
        return HttpResponse(
            status=204,
            headers={'HX-Trigger': 'conversationUnarchived'},
        )


class MuteConversationView(LoginRequiredMixin, View):
    """Wycisza konwersację."""

    def post(self, request, conversation_id):
        mute = request.POST.get('mute', 'true') == 'true'
        MessagingService.mute_conversation(conversation_id, request.user, mute)
        return HttpResponse(
            status=204,
            headers={'HX-Trigger': 'conversationMuted'},
        )


class UnreadCountView(LoginRequiredMixin, View):
    """Zwraca liczbę nieprzeczytanych wiadomości."""

    def get(self, request):
        count = MessagingService.get_unread_count(request.user)
        return JsonResponse({'count': count})
