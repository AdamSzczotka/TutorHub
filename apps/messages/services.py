from django.db import transaction
from django.db.models import Count, Prefetch, Q
from django.utils import timezone

from .models import (
    Conversation,
    ConversationParticipant,
    Message,
    MessageAttachment,
    MessageReadReceipt,
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
        initial_message: str | None = None,
    ) -> tuple['Conversation', bool]:
        """Tworzy nową konwersację.

        Args:
            creator: Użytkownik tworzący konwersację.
            participant_ids: Lista ID uczestników.
            subject: Temat konwersacji.
            is_group_chat: Czy to czat grupowy.
            initial_message: Opcjonalna pierwsza wiadomość.

        Returns:
            Krotka (konwersacja, czy_nowa).
        """
        # Dla konwersacji 1-1 sprawdź czy już istnieje
        if not is_group_chat and len(participant_ids) == 1:
            existing = cls._find_existing_direct_conversation(
                creator.id, participant_ids[0]
            )
            if existing:
                return existing, False

        conversation = Conversation.objects.create(
            subject=subject,
            is_group_chat=is_group_chat,
        )

        # Dodaj twórcę jako uczestnika
        ConversationParticipant.objects.create(
            conversation=conversation,
            user=creator,
        )

        # Dodaj pozostałych uczestników
        for user_id in participant_ids:
            if str(user_id) != str(creator.id):
                ConversationParticipant.objects.create(
                    conversation=conversation,
                    user_id=user_id,
                )

        # Wyślij początkową wiadomość
        if initial_message:
            cls.send_message(
                conversation=conversation,
                sender=creator,
                content=initial_message,
            )

        return conversation, True

    @classmethod
    def _find_existing_direct_conversation(cls, user1_id, user2_id):
        """Znajduje istniejącą konwersację 1-1."""
        conversations = (
            Conversation.objects.filter(
                is_group_chat=False,
                participants__user_id=user1_id,
            )
            .filter(
                participants__user_id=user2_id,
            )
            .annotate(participant_count=Count('participants'))
            .filter(participant_count=2)
            .first()
        )

        return conversations

    @classmethod
    @transaction.atomic
    def send_message(
        cls,
        conversation: Conversation,
        sender,
        content: str,
        content_type: str = 'TEXT',
        reply_to_id: str | None = None,
        attachments: list | None = None,
    ) -> Message:
        """Wysyła wiadomość w konwersacji.

        Args:
            conversation: Konwersacja do której wysyłamy.
            sender: Nadawca wiadomości.
            content: Treść wiadomości.
            content_type: Typ treści.
            reply_to_id: ID wiadomości na którą odpowiadamy.
            attachments: Lista załączników.

        Returns:
            Utworzona wiadomość.

        Raises:
            ValueError: Gdy nadawca nie jest uczestnikiem.
        """
        # Sprawdź czy nadawca jest uczestnikiem
        if not ConversationParticipant.objects.filter(
            conversation=conversation,
            user=sender,
            left_at__isnull=True,
        ).exists():
            raise ValueError('Nie jesteś uczestnikiem tej konwersacji')

        message = Message.objects.create(
            conversation=conversation,
            sender=sender,
            content=content,
            content_type=content_type,
            reply_to_id=reply_to_id,
        )

        # Dodaj załączniki
        if attachments:
            for attachment_data in attachments:
                MessageAttachment.objects.create(
                    message=message,
                    file_name=attachment_data['file_name'],
                    file=attachment_data['file'],
                    file_size=attachment_data['file_size'],
                    mime_type=attachment_data['mime_type'],
                )

        # Aktualizuj czas ostatniej wiadomości
        conversation.last_message_at = timezone.now()
        conversation.save(update_fields=['last_message_at'])

        # Automatycznie oznacz jako przeczytane dla nadawcy
        MessageReadReceipt.objects.create(
            message=message,
            user=sender,
        )

        return message

    @classmethod
    def get_user_conversations(cls, user, include_archived: bool = False):
        """Pobiera konwersacje użytkownika.

        Args:
            user: Użytkownik.
            include_archived: Czy uwzględnić zarchiwizowane.

        Returns:
            QuerySet konwersacji.
        """
        queryset = Conversation.objects.filter(
            participants__user=user,
            participants__left_at__isnull=True,
        )

        if not include_archived:
            queryset = queryset.filter(participants__is_archived=False)

        # Prefetch dla optymalizacji
        queryset = (
            queryset.prefetch_related(
                Prefetch(
                    'participants',
                    queryset=ConversationParticipant.objects.select_related('user'),
                ),
                Prefetch(
                    'messages',
                    queryset=Message.objects.filter(is_deleted=False).order_by(
                        '-created_at'
                    )[:1],
                ),
            )
            .annotate(
                unread_count=Count(
                    'messages',
                    filter=Q(messages__is_deleted=False)
                    & ~Q(messages__read_receipts__user=user),
                )
            )
            .order_by('-last_message_at')
        )

        return queryset

    @classmethod
    def get_conversation_messages(
        cls,
        conversation_id: str,
        user,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Message]:
        """Pobiera wiadomości z konwersacji.

        Args:
            conversation_id: ID konwersacji.
            user: Użytkownik pobierający wiadomości.
            limit: Maksymalna liczba wiadomości.
            offset: Przesunięcie.

        Returns:
            Lista wiadomości.

        Raises:
            PermissionError: Gdy brak dostępu.
        """
        # Sprawdź uprawnienia
        if not ConversationParticipant.objects.filter(
            conversation_id=conversation_id,
            user=user,
            left_at__isnull=True,
        ).exists():
            raise PermissionError('Brak dostępu do konwersacji')

        messages = (
            Message.objects.filter(
                conversation_id=conversation_id,
                is_deleted=False,
            )
            .select_related(
                'sender',
                'reply_to',
                'reply_to__sender',
            )
            .prefetch_related(
                'attachments',
                'read_receipts',
            )
            .order_by('-created_at')[offset : offset + limit]
        )

        return list(reversed(messages))

    @classmethod
    def mark_as_read(cls, message_ids: list, user) -> int:
        """Oznacza wiadomości jako przeczytane.

        Args:
            message_ids: Lista ID wiadomości.
            user: Użytkownik.

        Returns:
            Liczba nowo oznaczonych wiadomości.
        """
        created_count = 0
        for message_id in message_ids:
            _, created = MessageReadReceipt.objects.get_or_create(
                message_id=message_id,
                user=user,
            )
            if created:
                created_count += 1

        # Aktualizuj last_read_at uczestnika
        conversations = Message.objects.filter(id__in=message_ids).values_list(
            'conversation_id', flat=True
        ).distinct()

        ConversationParticipant.objects.filter(
            conversation_id__in=conversations,
            user=user,
        ).update(last_read_at=timezone.now())

        return created_count

    @classmethod
    def edit_message(cls, message_id: str, user, new_content: str) -> Message:
        """Edytuje wiadomość.

        Args:
            message_id: ID wiadomości.
            user: Użytkownik edytujący.
            new_content: Nowa treść.

        Returns:
            Zaktualizowana wiadomość.

        Raises:
            PermissionError: Gdy brak uprawnień.
        """
        message = Message.objects.get(id=message_id)

        if message.sender != user:
            raise PermissionError('Możesz edytować tylko własne wiadomości')

        message.content = new_content
        message.is_edited = True
        message.edited_at = timezone.now()
        message.save(update_fields=['content', 'is_edited', 'edited_at', 'updated_at'])

        return message

    @classmethod
    def delete_message(cls, message_id: str, user) -> bool:
        """Usuwa wiadomość (soft delete).

        Args:
            message_id: ID wiadomości.
            user: Użytkownik usuwający.

        Returns:
            True jeśli usunięto.

        Raises:
            PermissionError: Gdy brak uprawnień.
        """
        message = Message.objects.get(id=message_id)

        if message.sender != user:
            raise PermissionError('Możesz usunąć tylko własne wiadomości')

        message.is_deleted = True
        message.deleted_at = timezone.now()
        message.save(update_fields=['is_deleted', 'deleted_at', 'updated_at'])

        return True

    @classmethod
    def search_messages(
        cls,
        user,
        query: str,
        conversation_id: str | None = None,
        sender_id: str | None = None,
        start_date=None,
        end_date=None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict:
        """Wyszukuje wiadomości.

        Args:
            user: Użytkownik wyszukujący.
            query: Fraza wyszukiwania.
            conversation_id: Opcjonalne ID konwersacji.
            sender_id: Opcjonalne ID nadawcy.
            start_date: Data początkowa.
            end_date: Data końcowa.
            limit: Limit wyników.
            offset: Przesunięcie.

        Returns:
            Słownik z wynikami, liczba wszystkich i czy jest więcej.
        """
        # Bazowy queryset - tylko konwersacje użytkownika
        user_conversations = ConversationParticipant.objects.filter(
            user=user,
            left_at__isnull=True,
        ).values_list('conversation_id', flat=True)

        queryset = Message.objects.filter(
            conversation_id__in=user_conversations,
            is_deleted=False,
            content__icontains=query,
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
        messages = queryset.select_related('sender', 'conversation').prefetch_related(
            'attachments'
        )[offset : offset + limit]

        return {
            'messages': messages,
            'total_count': total_count,
            'has_more': offset + limit < total_count,
        }

    @classmethod
    def archive_conversation(cls, conversation_id: str, user) -> None:
        """Archiwizuje konwersację dla użytkownika.

        Args:
            conversation_id: ID konwersacji.
            user: Użytkownik.
        """
        ConversationParticipant.objects.filter(
            conversation_id=conversation_id,
            user=user,
        ).update(is_archived=True)

    @classmethod
    def unarchive_conversation(cls, conversation_id: str, user) -> None:
        """Przywraca konwersację z archiwum.

        Args:
            conversation_id: ID konwersacji.
            user: Użytkownik.
        """
        ConversationParticipant.objects.filter(
            conversation_id=conversation_id,
            user=user,
        ).update(is_archived=False)

    @classmethod
    def mute_conversation(cls, conversation_id: str, user, mute: bool = True) -> None:
        """Wycisza/odcisza konwersację.

        Args:
            conversation_id: ID konwersacji.
            user: Użytkownik.
            mute: Czy wyciszyć.
        """
        ConversationParticipant.objects.filter(
            conversation_id=conversation_id,
            user=user,
        ).update(is_muted=mute)

    @classmethod
    def get_unread_count(cls, user) -> int:
        """Pobiera liczbę nieprzeczytanych wiadomości.

        Args:
            user: Użytkownik.

        Returns:
            Liczba nieprzeczytanych wiadomości.
        """
        user_conversations = ConversationParticipant.objects.filter(
            user=user,
            left_at__isnull=True,
            is_archived=False,
        ).values_list('conversation_id', flat=True)

        return (
            Message.objects.filter(
                conversation_id__in=user_conversations,
                is_deleted=False,
            )
            .exclude(read_receipts__user=user)
            .exclude(sender=user)
            .count()
        )
