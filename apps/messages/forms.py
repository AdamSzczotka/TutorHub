from django import forms
from django.contrib.auth import get_user_model

from .models import MessageContentType

User = get_user_model()


class ConversationForm(forms.Form):
    """Formularz tworzenia konwersacji."""

    participants = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True),
        widget=forms.SelectMultiple(
            attrs={
                'class': 'select select-bordered w-full',
                'x-data': '',
                'x-init': "new TomSelect($el, {plugins: ['remove_button']})",
            }
        ),
        label='Uczestnicy',
        help_text='Wybierz uczestników konwersacji',
    )
    subject = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(
            attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Temat konwersacji (opcjonalnie)',
            }
        ),
        label='Temat',
    )
    initial_message = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 3,
                'placeholder': 'Pierwsza wiadomość (opcjonalnie)',
            }
        ),
        label='Wiadomość początkowa',
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            # Wyklucz bieżącego użytkownika z listy uczestników
            self.fields['participants'].queryset = User.objects.filter(
                is_active=True
            ).exclude(id=user.id)


class MessageForm(forms.Form):
    """Formularz wysyłania wiadomości."""

    content = forms.CharField(
        widget=forms.Textarea(
            attrs={
                'class': 'textarea textarea-bordered w-full resize-none',
                'rows': 3,
                'placeholder': 'Wpisz wiadomość...',
                'x-model': 'content',
                'x-on:keydown.ctrl.enter': '$refs.submitBtn.click()',
            }
        ),
        label='Treść',
    )
    content_type = forms.ChoiceField(
        choices=MessageContentType.choices,
        initial=MessageContentType.TEXT,
        required=False,
        widget=forms.HiddenInput(),
    )
    reply_to = forms.UUIDField(
        required=False,
        widget=forms.HiddenInput(),
    )
    def clean(self):
        """Waliduje formularz i załączniki."""
        cleaned_data = super().clean()
        files = self.files.getlist('attachments')

        if len(files) > 5:
            raise forms.ValidationError('Maksymalnie 5 załączników')

        max_size = 10 * 1024 * 1024  # 10MB
        for file in files:
            if file.size > max_size:
                raise forms.ValidationError(f'Plik {file.name} przekracza limit 10MB')

        return cleaned_data


class MessageEditForm(forms.Form):
    """Formularz edycji wiadomości."""

    content = forms.CharField(
        widget=forms.Textarea(
            attrs={
                'class': 'textarea textarea-bordered w-full resize-none',
                'rows': 3,
            }
        ),
        label='Treść',
    )
