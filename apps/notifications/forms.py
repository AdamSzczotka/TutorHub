from django import forms

from apps.accounts.models import NotificationPreference

from .models import AnnouncementType


class NotificationPreferenceForm(forms.ModelForm):
    """Formularz preferencji powiadomień.

    Uses NotificationPreference model from accounts app.
    """

    class Meta:
        model = NotificationPreference
        exclude = ['user', 'created_at', 'updated_at']
        widgets = {
            'quiet_hours_start': forms.TimeInput(
                attrs={
                    'class': 'input input-bordered w-full',
                    'type': 'time',
                }
            ),
            'quiet_hours_end': forms.TimeInput(
                attrs={
                    'class': 'input input-bordered w-full',
                    'type': 'time',
                }
            ),
            'reminder_hours_before': forms.NumberInput(
                attrs={
                    'class': 'input input-bordered w-full',
                    'min': '1',
                    'max': '72',
                }
            ),
        }


class AnnouncementForm(forms.Form):
    """Formularz tworzenia ogłoszenia."""

    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(
            attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Tytuł ogłoszenia',
            }
        ),
        label='Tytuł',
    )
    content = forms.CharField(
        widget=forms.Textarea(
            attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 5,
                'placeholder': 'Treść ogłoszenia',
            }
        ),
        label='Treść',
    )
    type = forms.ChoiceField(
        choices=AnnouncementType.choices,
        initial=AnnouncementType.INFO,
        widget=forms.Select(attrs={'class': 'select select-bordered w-full'}),
        label='Typ',
    )
    target_roles = forms.MultipleChoiceField(
        choices=[
            ('ADMIN', 'Administratorzy'),
            ('TUTOR', 'Korepetytorzy'),
            ('STUDENT', 'Uczniowie'),
        ],
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'checkbox'}),
        label='Widoczne dla',
        help_text='Zostaw puste aby wyświetlić wszystkim',
    )
    is_pinned = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'checkbox'}),
        label='Przypnij na górze',
    )
    expires_at = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(
            attrs={
                'class': 'input input-bordered w-full',
                'type': 'datetime-local',
            }
        ),
        label='Data wygaśnięcia',
    )
    notify_users = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'checkbox'}),
        label='Wyślij powiadomienie do użytkowników',
    )
