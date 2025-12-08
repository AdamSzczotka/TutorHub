import pytest
from django.urls import reverse

from apps.accounts.models import User
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
def authenticated_client(client, user1):
    client.login(email='user1@test.com', password='testpass123')
    return client


@pytest.mark.django_db
class TestConversationListView:
    def test_requires_login(self, client):
        """Test że widok wymaga logowania."""
        url = reverse('messages:list')
        response = client.get(url)
        assert response.status_code == 302
        assert 'login' in response.url.lower()

    def test_shows_conversations(self, authenticated_client, user1, user2):
        """Test wyświetlania listy konwersacji."""
        MessagingService.create_conversation(
            creator=user1,
            participant_ids=[user2.id],
            subject='Test conversation',
        )

        url = reverse('messages:list')
        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert 'Test conversation' in response.content.decode()


@pytest.mark.django_db
class TestConversationDetailView:
    def test_requires_login(self, client, user1, user2):
        """Test że widok wymaga logowania."""
        conversation, _ = MessagingService.create_conversation(
            creator=user1,
            participant_ids=[user2.id],
        )

        url = reverse('messages:detail', args=[conversation.id])
        response = client.get(url)

        assert response.status_code == 302

    def test_shows_conversation_detail(self, authenticated_client, user1, user2):
        """Test wyświetlania szczegółów konwersacji."""
        conversation, _ = MessagingService.create_conversation(
            creator=user1,
            participant_ids=[user2.id],
        )
        MessagingService.send_message(
            conversation=conversation,
            sender=user1,
            content='Hello!',
        )

        url = reverse('messages:detail', args=[conversation.id])
        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert 'Hello!' in response.content.decode()


@pytest.mark.django_db
class TestSendMessageView:
    def test_send_message(self, authenticated_client, user1, user2):
        """Test wysyłania wiadomości przez widok."""
        conversation, _ = MessagingService.create_conversation(
            creator=user1,
            participant_ids=[user2.id],
        )

        url = reverse('messages:send', args=[conversation.id])
        response = authenticated_client.post(
            url,
            {'content': 'New message'},
        )

        assert response.status_code == 200
        assert conversation.messages.filter(content='New message').exists()


@pytest.mark.django_db
class TestSearchMessagesView:
    def test_search_requires_min_query(self, authenticated_client, user1, user2):
        """Test że wyszukiwanie wymaga minimum 2 znaków."""
        url = reverse('messages:search') + '?q=a'
        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert response.content.decode() == ''

    def test_search_returns_results(self, authenticated_client, user1, user2):
        """Test zwracania wyników wyszukiwania."""
        conversation, _ = MessagingService.create_conversation(
            creator=user1,
            participant_ids=[user2.id],
        )
        MessagingService.send_message(
            conversation=conversation,
            sender=user1,
            content='Unique searchable content',
        )

        url = reverse('messages:search') + '?q=searchable'
        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert 'searchable' in response.content.decode().lower()


@pytest.mark.django_db
class TestUnreadCountView:
    def test_returns_unread_count(self, authenticated_client, user1, user2):
        """Test zwracania liczby nieprzeczytanych."""
        conversation, _ = MessagingService.create_conversation(
            creator=user2,
            participant_ids=[user1.id],
        )
        MessagingService.send_message(
            conversation=conversation,
            sender=user2,
            content='Unread message',
        )

        url = reverse('messages:unread_count')
        response = authenticated_client.get(url)

        assert response.status_code == 200
        data = response.json()
        assert data['count'] == 1
