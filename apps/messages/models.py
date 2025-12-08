import uuid

from django.conf import settings
from django.db import models


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

    created_at = models.DateTimeField('Utworzono', auto_now_add=True)
    updated_at = models.DateTimeField('Zaktualizowano', auto_now=True)
    last_message_at = models.DateTimeField('Ostatnia wiadomość', auto_now_add=True)

    class Meta:
        db_table = 'conversations'
        verbose_name = 'Konwersacja'
        verbose_name_plural = 'Konwersacje'
        ordering = ['-last_message_at']

    def __str__(self):
        return self.subject or f'Konwersacja {self.id}'


class ConversationParticipant(models.Model):
    """Uczestnik konwersacji."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='participants',
        verbose_name='Konwersacja',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='conversation_participations',
        verbose_name='Użytkownik',
    )

    joined_at = models.DateTimeField('Dołączono', auto_now_add=True)
    left_at = models.DateTimeField('Opuszczono', null=True, blank=True)
    last_read_at = models.DateTimeField('Ostatnio przeczytano', null=True, blank=True)
    is_archived = models.BooleanField('Zarchiwizowana', default=False)
    is_muted = models.BooleanField('Wyciszona', default=False)

    class Meta:
        db_table = 'conversation_participants'
        verbose_name = 'Uczestnik konwersacji'
        verbose_name_plural = 'Uczestnicy konwersacji'
        unique_together = ['conversation', 'user']
        indexes = [
            models.Index(fields=['user', 'conversation']),
            models.Index(fields=['last_read_at']),
        ]

    def __str__(self):
        return f'{self.user} w {self.conversation}'


class Message(models.Model):
    """Model wiadomości."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='Konwersacja',
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        verbose_name='Nadawca',
    )

    # Content
    content = models.TextField('Treść')
    content_type = models.CharField(
        'Typ treści',
        max_length=20,
        choices=MessageContentType.choices,
        default=MessageContentType.TEXT,
    )

    # Metadata
    is_edited = models.BooleanField('Edytowana', default=False)
    edited_at = models.DateTimeField('Data edycji', null=True, blank=True)
    is_deleted = models.BooleanField('Usunięta', default=False)
    deleted_at = models.DateTimeField('Data usunięcia', null=True, blank=True)

    # Threading
    reply_to = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='replies',
        verbose_name='Odpowiedź na',
    )

    created_at = models.DateTimeField('Utworzono', auto_now_add=True)
    updated_at = models.DateTimeField('Zaktualizowano', auto_now=True)

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
        return f'Wiadomość od {self.sender} - {self.created_at}'


class MessageAttachment(models.Model):
    """Załącznik do wiadomości."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name='Wiadomość',
    )

    file_name = models.CharField('Nazwa pliku', max_length=255)
    file = models.FileField('Plik', upload_to='message_attachments/%Y/%m/')
    file_size = models.PositiveIntegerField('Rozmiar (bytes)')
    mime_type = models.CharField('Typ MIME', max_length=100)

    uploaded_at = models.DateTimeField('Przesłano', auto_now_add=True)

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
        related_name='read_receipts',
        verbose_name='Wiadomość',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='message_read_receipts',
        verbose_name='Użytkownik',
    )
    read_at = models.DateTimeField('Przeczytano', auto_now_add=True)

    class Meta:
        db_table = 'message_read_receipts'
        verbose_name = 'Potwierdzenie odczytu'
        verbose_name_plural = 'Potwierdzenia odczytu'
        unique_together = ['message', 'user']
        indexes = [
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f'{self.user} przeczytał {self.message}'
