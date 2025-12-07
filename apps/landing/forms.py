"""Forms for landing app CMS."""

from django import forms

from .models import FAQItem, Lead, PageContent, SchoolInfo, TeamMember, Testimonial


class ContactForm(forms.ModelForm):
    """Contact form with GDPR consent."""

    gdpr_consent = forms.BooleanField(
        label='Wyrażam zgodę na przetwarzanie danych osobowych',
        required=True,
    )

    class Meta:
        model = Lead
        fields = [
            'name',
            'email',
            'phone',
            'subject',
            'message',
            'gdpr_consent',
            'marketing_consent',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Imię i nazwisko',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Email',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Telefon',
            }),
            'subject': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Temat',
            }),
            'message': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 4,
                'placeholder': 'Wiadomość',
            }),
        }
        labels = {
            'marketing_consent': 'Wyrażam zgodę na otrzymywanie informacji marketingowych',
        }


# =============================================================================
# CMS Admin Forms
# =============================================================================


class PageContentForm(forms.ModelForm):
    """Form for editing landing page content sections."""

    class Meta:
        model = PageContent
        fields = ['page_key', 'title', 'subtitle', 'content', 'is_active']
        widgets = {
            'page_key': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'np. hero, about, features',
            }),
            'title': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Tytuł sekcji',
            }),
            'subtitle': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Podtytuł sekcji',
            }),
            'content': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 10,
                'placeholder': 'Treść sekcji (HTML dozwolony)',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'toggle toggle-primary',
            }),
        }


class TeamMemberForm(forms.ModelForm):
    """Form for managing team members."""

    expertise_text = forms.CharField(
        label='Specjalizacje',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'textarea textarea-bordered w-full',
            'rows': 3,
            'placeholder': 'Jedna specjalizacja na linię, np.:\nMatematyka\nFizyka\nChemia',
        }),
        help_text='Wpisz każdą specjalizację w nowej linii',
    )

    class Meta:
        model = TeamMember
        fields = [
            'user',
            'name',
            'surname',
            'position',
            'bio',
            'image',
            'order_index',
            'is_published',
        ]
        widgets = {
            'user': forms.Select(attrs={
                'class': 'select select-bordered w-full',
            }),
            'name': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Imię',
            }),
            'surname': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Nazwisko',
            }),
            'position': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'np. Korepetytor matematyki',
            }),
            'bio': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 4,
                'placeholder': 'Krótki opis osoby...',
            }),
            'image': forms.FileInput(attrs={
                'class': 'file-input file-input-bordered w-full',
                'accept': 'image/*',
            }),
            'order_index': forms.NumberInput(attrs={
                'class': 'input input-bordered w-full',
                'min': 0,
            }),
            'is_published': forms.CheckboxInput(attrs={
                'class': 'toggle toggle-primary',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Convert list to text for editing
            self.fields['expertise_text'].initial = '\n'.join(
                self.instance.expertise or []
            )

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Convert text to list
        expertise_text = self.cleaned_data.get('expertise_text', '')
        instance.expertise = [
            line.strip()
            for line in expertise_text.split('\n')
            if line.strip()
        ]
        if commit:
            instance.save()
        return instance


class TestimonialForm(forms.ModelForm):
    """Form for managing testimonials."""

    class Meta:
        model = Testimonial
        fields = [
            'student_name',
            'parent_name',
            'content',
            'rating',
            'subject',
            'level',
            'image',
            'is_verified',
            'is_published',
            'display_order',
        ]
        widgets = {
            'student_name': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Imię ucznia',
            }),
            'parent_name': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Imię rodzica (opcjonalne)',
            }),
            'content': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 4,
                'placeholder': 'Treść opinii...',
            }),
            'rating': forms.NumberInput(attrs={
                'class': 'input input-bordered w-full',
                'min': 1,
                'max': 5,
            }),
            'subject': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'np. Matematyka',
            }),
            'level': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'np. Liceum, Szkoła podstawowa',
            }),
            'image': forms.FileInput(attrs={
                'class': 'file-input file-input-bordered w-full',
                'accept': 'image/*',
            }),
            'is_verified': forms.CheckboxInput(attrs={
                'class': 'toggle toggle-success',
            }),
            'is_published': forms.CheckboxInput(attrs={
                'class': 'toggle toggle-primary',
            }),
            'display_order': forms.NumberInput(attrs={
                'class': 'input input-bordered w-full',
                'min': 0,
            }),
        }


class FAQItemForm(forms.ModelForm):
    """Form for managing FAQ items."""

    class Meta:
        model = FAQItem
        fields = ['question', 'answer', 'category', 'order_index', 'is_published']
        widgets = {
            'question': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Pytanie',
            }),
            'answer': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 4,
                'placeholder': 'Odpowiedź na pytanie...',
            }),
            'category': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'np. Płatności, Zajęcia',
            }),
            'order_index': forms.NumberInput(attrs={
                'class': 'input input-bordered w-full',
                'min': 0,
            }),
            'is_published': forms.CheckboxInput(attrs={
                'class': 'toggle toggle-primary',
            }),
        }


class SchoolInfoForm(forms.ModelForm):
    """Form for managing school information."""

    class Meta:
        model = SchoolInfo
        fields = [
            'name',
            'tagline',
            'description',
            'email',
            'phone',
            'address',
            'city',
            'postal_code',
            'latitude',
            'longitude',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Nazwa szkoły',
            }),
            'tagline': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Slogan szkoły',
            }),
            'description': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 4,
                'placeholder': 'Opis szkoły...',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'kontakt@napiatke.pl',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': '+48 123 456 789',
            }),
            'address': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'ul. Przykładowa 1',
            }),
            'city': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Miasto',
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': '00-000',
            }),
            'latitude': forms.NumberInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': '52.2297',
                'step': '0.00000001',
            }),
            'longitude': forms.NumberInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': '21.0122',
                'step': '0.00000001',
            }),
        }


class LeadStatusForm(forms.ModelForm):
    """Form for updating lead status."""

    class Meta:
        model = Lead
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={
                'class': 'select select-bordered w-full',
            }),
        }
