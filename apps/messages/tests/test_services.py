import pytest

from apps.accounts.models import User
from apps.messages.models import Conversation, ConversationParticipant, Message
from apps.messages.services import MessagingService


@pytest.fixture
def user1(db):
    return User.objects.create_user(
        email='user1@test.com',
        password='testpass123',
        first_name='User',
        last_name='One',
    )


@pytest.fixture
def user2(db):
    return User.objects.create_user(
        email='user2@test.com',
        password='testpass123',
        first_name='User',
        last_name='Two',
    )


@pytest.fixture
def user3(db):
    return User.objects.create_user(
        email='user3@test.com',
        password='testpass123',
        first_name='User',
        last_name='Three',
    )


@pytest.mark.django_db
class TestMessagingService:
    def test_create_conversation(self, user1, user2):
        """Test tworzenia konwersacji."""
        conversation, is_new = MessagingService.create_conversation(
            creator=user1,
            participant_ids=[user2.id],
            subject='Test conversation',
        )

        assert is_new is True
        assert conversation.subject == 'Test conversation'
        assert conversation.participants.count() == 2

    def test_create_conversation_returns_existing(self, user1, user2):
        """Test że ta sama konwersacja 1-1 nie jest duplikowana."""
        conversation1, is_new1 = MessagingService.create_conversation(
            creator=user1,
            participant_ids=[user2.id],
        )

        conversation2, is_new2 = MessagingService.create_conversation(
            creator=user2,
            participant_ids=[user1.id],
        )

        assert is_new1 is True
        assert is_new2 is False
        assert conversation1.id == conversation2.id

    def test_create_group_conversation(self, user1, user2, user3):
        """Test tworzenia konwersacji grupowej."""
        conversation, is_new = MessagingService.create_conversation(
            creator=user1,
            participant_ids=[user2.id, user3.id],
            subject='Group chat',
            is_group_chat=True,
        )

        assert is_new is True
        assert conversation.is_group_chat is True
        assert conversation.participants.count() == 3

    def test_send_message(self, user1, user2):
        """Test wysyłania wiadomości."""
        conversation, _ = MessagingService.create_conversation(
            creator=user1,
            participant_ids=[user2.id],
        )

        message = MessagingService.send_message(
            conversation=conversation,
            sender=user1,
            content='Hello!',
        )

        assert message.content == 'Hello!'
        assert message.sender == user1
        assert message.conversation == conversation

    def test_send_message_not_participant(self, user1, user2, user3):
        """Test że non-participant nie może wysłać wiadomości."""
        conversation, _ = MessagingService.create_conversation(
            creator=user1,
            participant_ids=[user2.id],
        )

        with pytest.raises(ValueError, match='Nie jesteś uczestnikiem'):
            MessagingService.send_message(
                conversation=conversation,
                sender=user3,
                content='Should fail',
            )

    def test_get_user_conversations(self, user1, user2, user3):
        """Test pobierania konwersacji użytkownika."""
        MessagingService.create_conversation(
            creator=user1,
            participant_ids=[user2.id],
        )
        MessagingService.create_conversation(
            creator=user1,
            participant_ids=[user3.id],
        )

        conversations = MessagingService.get_user_conversations(user1)

        assert conversations.count() == 2

    def test_get_conversation_messages(self, user1, user2):
        """Test pobierania wiadomości z konwersacji."""
        conversation, _ = MessagingService.create_conversation(
            creator=user1,
            participant_ids=[user2.id],
        )

        MessagingService.send_message(
            conversation=conversation,
            sender=user1,
            content='Message 1',
        )
        MessagingService.send_message(
            conversation=conversation,
            sender=user2,
            content='Message 2',
        )

        messages = MessagingService.get_conversation_messages(
            conversation_id=str(conversation.id),
            user=user1,
        )

        assert len(messages) == 2
        assert messages[0].content == 'Message 1'
        assert messages[1].content == 'Message 2'

    def test_mark_as_read(self, user1, user2):
        """Test oznaczania wiadomości jako przeczytane."""
        conversation, _ = MessagingService.create_conversation(
            creator=user1,
            participant_ids=[user2.id],
        )

        message = MessagingService.send_message(
            conversation=conversation,
            sender=user1,
            content='Read me',
        )

        count = MessagingService.mark_as_read([str(message.id)], user2)

        assert count == 1
        assert message.read_receipts.filter(user=user2).exists()

    def test_edit_message(self, user1, user2):
        """Test edycji wiadomości."""
        conversation, _ = MessagingService.create_conversation(
            creator=user1,
            participant_ids=[user2.id],
        )

        message = MessagingService.send_message(
            conversation=conversation,
            sender=user1,
            content='Original',
        )

        updated = MessagingService.edit_message(
            message_id=str(message.id),
            user=user1,
            new_content='Edited',
        )

        assert updated.content == 'Edited'
        assert updated.is_edited is True

    def test_edit_message_not_sender(self, user1, user2):
        """Test że inny użytkownik nie może edytować."""
        conversation, _ = MessagingService.create_conversation(
            creator=user1,
            participant_ids=[user2.id],
        )

        message = MessagingService.send_message(
            conversation=conversation,
            sender=user1,
            content='Original',
        )

        with pytest.raises(PermissionError):
            MessagingService.edit_message(
                message_id=str(message.id),
                user=user2,
                new_content='Edited',
            )

    def test_delete_message(self, user1, user2):
        """Test usuwania wiadomości."""
        conversation, _ = MessagingService.create_conversation(
            creator=user1,
            participant_ids=[user2.id],
        )

        message = MessagingService.send_message(
            conversation=conversation,
            sender=user1,
            content='Delete me',
        )

        result = MessagingService.delete_message(
            message_id=str(message.id),
            user=user1,
        )

        message.refresh_from_db()
        assert result is True
        assert message.is_deleted is True

    def test_search_messages(self, user1, user2):
        """Test wyszukiwania wiadomości."""
        conversation, _ = MessagingService.create_conversation(
            creator=user1,
            participant_ids=[user2.id],
        )

        MessagingService.send_message(
            conversation=conversation,
            sender=user1,
            content='Hello world',
        )
        MessagingService.send_message(
            conversation=conversation,
            sender=user2,
            content='Goodbye world',
        )
        MessagingService.send_message(
            conversation=conversation,
            sender=user1,
            content='Python code',
        )

        results = MessagingService.search_messages(
            user=user1,
            query='world',
        )

        assert results['total_count'] == 2

    def test_archive_conversation(self, user1, user2):
        """Test archiwizacji konwersacji."""
        conversation, _ = MessagingService.create_conversation(
            creator=user1,
            participant_ids=[user2.id],
        )

        MessagingService.archive_conversation(str(conversation.id), user1)

        participant = ConversationParticipant.objects.get(
            conversation=conversation, user=user1
        )
        assert participant.is_archived is True

    def test_unread_count(self, user1, user2):
        """Test liczenia nieprzeczytanych wiadomości."""
        conversation, _ = MessagingService.create_conversation(
            creator=user1,
            participant_ids=[user2.id],
        )

        MessagingService.send_message(
            conversation=conversation,
            sender=user1,
            content='Message 1',
        )
        MessagingService.send_message(
            conversation=conversation,
            sender=user1,
            content='Message 2',
        )

        count = MessagingService.get_unread_count(user2)

        assert count == 2
