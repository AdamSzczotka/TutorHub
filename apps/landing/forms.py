"""Forms for landing app CMS."""

from django import forms

from .models import (
    EducationLevel,
    FAQItem,
    LandingStatistic,
    LandingSubject,
    Lead,
    LessonType,
    PageContent,
    PricingPackage,
    SchoolInfo,
    TeamMember,
    Testimonial,
    WhyUsCard,
)


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
            'logo',
            'logo_dark',
            'favicon',
            'email',
            'phone',
            'phone_secondary',
            'address',
            'city',
            'postal_code',
            'latitude',
            'longitude',
            'footer_text',
            'copyright_text',
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
            'logo': forms.FileInput(attrs={
                'class': 'file-input file-input-bordered w-full',
                'accept': 'image/*',
            }),
            'logo_dark': forms.FileInput(attrs={
                'class': 'file-input file-input-bordered w-full',
                'accept': 'image/*',
            }),
            'favicon': forms.FileInput(attrs={
                'class': 'file-input file-input-bordered w-full',
                'accept': 'image/*',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'kontakt@napiatke.pl',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': '+48 123 456 789',
            }),
            'phone_secondary': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': '+48 987 654 321',
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
            'footer_text': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 3,
                'placeholder': 'Tekst wyświetlany w stopce...',
            }),
            'copyright_text': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': '© 2024 Na Piątkę. Wszelkie prawa zastrzeżone.',
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


# =============================================================================
# New CMS Forms for Landing Page Sections
# =============================================================================


class LandingStatisticForm(forms.ModelForm):
    """Form for managing landing page statistics."""

    class Meta:
        model = LandingStatistic
        fields = ['value', 'label', 'description', 'order_index', 'is_published']
        widgets = {
            'value': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'np. 5+, 100+, 3',
            }),
            'label': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'np. lat doświadczenia',
            }),
            'description': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Dodatkowy opis (opcjonalnie)',
            }),
            'order_index': forms.NumberInput(attrs={
                'class': 'input input-bordered w-full',
                'min': 0,
            }),
            'is_published': forms.CheckboxInput(attrs={
                'class': 'toggle toggle-primary',
            }),
        }


class WhyUsCardForm(forms.ModelForm):
    """Form for managing 'Why Us' cards."""

    class Meta:
        model = WhyUsCard
        fields = ['title', 'description', 'icon', 'color', 'link', 'order_index', 'is_published']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'np. Małe grupy do 4 osób',
            }),
            'description': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 3,
                'placeholder': 'Opis korzyści...',
            }),
            'icon': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full font-mono text-sm',
                'rows': 3,
                'placeholder': '<svg>...</svg>',
            }),
            'color': forms.Select(
                choices=[
                    ('brand', 'Brand (niebieski)'),
                    ('emerald', 'Emerald (zielony)'),
                    ('blue', 'Blue (jasnoniebieski)'),
                    ('purple', 'Purple (fioletowy)'),
                    ('orange', 'Orange (pomarańczowy)'),
                    ('teal', 'Teal (morski)'),
                ],
                attrs={'class': 'select select-bordered w-full'},
            ),
            'link': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': '#pakiety lub /kontakt',
            }),
            'order_index': forms.NumberInput(attrs={
                'class': 'input input-bordered w-full',
                'min': 0,
            }),
            'is_published': forms.CheckboxInput(attrs={
                'class': 'toggle toggle-primary',
            }),
        }


class SubjectForm(forms.ModelForm):
    """Form for managing subjects."""

    topics_text = forms.CharField(
        label='Tematy',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'textarea textarea-bordered w-full',
            'rows': 4,
            'placeholder': 'Jeden temat na linię:\nArytmetyka\nAlgebra\nGeometria',
        }),
        help_text='Wpisz każdy temat w nowej linii',
    )

    target_groups_text = forms.CharField(
        label='Grupy docelowe',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'textarea textarea-bordered w-full',
            'rows': 3,
            'placeholder': 'Jedna grupa na linię:\nSzkoła podstawowa\nLiceum\nMatura',
        }),
        help_text='Wpisz każdą grupę w nowej linii',
    )

    class Meta:
        model = LandingSubject
        fields = [
            'name',
            'slug',
            'short_description',
            'full_description',
            'icon_svg',
            'color_from',
            'color_to',
            'levels',
            'order_index',
            'is_published',
            'is_featured',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'np. Matematyka',
            }),
            'slug': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'np. matematyka',
            }),
            'short_description': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 2,
                'placeholder': 'Krótki opis wyświetlany na karcie...',
            }),
            'full_description': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 4,
                'placeholder': 'Pełny opis wyświetlany w modalu...',
            }),
            'icon_svg': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full font-mono text-sm',
                'rows': 3,
                'placeholder': '<svg>...</svg>',
            }),
            'color_from': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'np. blue-500',
            }),
            'color_to': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'np. indigo-600',
            }),
            'levels': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'np. Wszystkie poziomy lub A1-C2',
            }),
            'order_index': forms.NumberInput(attrs={
                'class': 'input input-bordered w-full',
                'min': 0,
            }),
            'is_published': forms.CheckboxInput(attrs={
                'class': 'toggle toggle-primary',
            }),
            'is_featured': forms.CheckboxInput(attrs={
                'class': 'toggle toggle-secondary',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['topics_text'].initial = '\n'.join(self.instance.topics or [])
            self.fields['target_groups_text'].initial = '\n'.join(
                self.instance.target_groups or []
            )

    def save(self, commit=True):
        instance = super().save(commit=False)
        topics_text = self.cleaned_data.get('topics_text', '')
        instance.topics = [
            line.strip() for line in topics_text.split('\n') if line.strip()
        ]
        target_groups_text = self.cleaned_data.get('target_groups_text', '')
        instance.target_groups = [
            line.strip() for line in target_groups_text.split('\n') if line.strip()
        ]
        if commit:
            instance.save()
        return instance


class PricingPackageForm(forms.ModelForm):
    """Form for managing pricing packages."""

    class Meta:
        model = PricingPackage
        fields = [
            'name',
            'sessions_count',
            'individual_price',
            'group_price',
            'is_popular',
            'order_index',
            'is_published',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'np. Standard',
            }),
            'sessions_count': forms.NumberInput(attrs={
                'class': 'input input-bordered w-full',
                'min': 1,
                'placeholder': 'np. 8',
            }),
            'individual_price': forms.NumberInput(attrs={
                'class': 'input input-bordered w-full',
                'min': 0,
                'step': '0.01',
                'placeholder': 'np. 460.00',
            }),
            'group_price': forms.NumberInput(attrs={
                'class': 'input input-bordered w-full',
                'min': 0,
                'step': '0.01',
                'placeholder': 'np. 300.00',
            }),
            'is_popular': forms.CheckboxInput(attrs={
                'class': 'toggle toggle-success',
            }),
            'order_index': forms.NumberInput(attrs={
                'class': 'input input-bordered w-full',
                'min': 0,
            }),
            'is_published': forms.CheckboxInput(attrs={
                'class': 'toggle toggle-primary',
            }),
        }


class EducationLevelForm(forms.ModelForm):
    """Form for managing education levels."""

    class Meta:
        model = EducationLevel
        fields = ['name', 'icon_svg', 'color', 'order_index', 'is_published']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'np. Szkoła podstawowa',
            }),
            'icon_svg': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full font-mono text-sm',
                'rows': 2,
                'placeholder': '<svg>...</svg>',
            }),
            'color': forms.Select(
                choices=[
                    ('brand', 'Brand (niebieski)'),
                    ('emerald', 'Emerald (zielony)'),
                    ('blue', 'Blue (jasnoniebieski)'),
                    ('red', 'Red (czerwony)'),
                ],
                attrs={'class': 'select select-bordered w-full'},
            ),
            'order_index': forms.NumberInput(attrs={
                'class': 'input input-bordered w-full',
                'min': 0,
            }),
            'is_published': forms.CheckboxInput(attrs={
                'class': 'toggle toggle-primary',
            }),
        }


class LessonTypeForm(forms.ModelForm):
    """Form for managing lesson types."""

    features_text = forms.CharField(
        label='Cechy',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'textarea textarea-bordered w-full',
            'rows': 4,
            'placeholder': 'Jedna cecha na linię:\nIndywidualny program\nElastyczne tempo\n100% uwagi',
        }),
        help_text='Wpisz każdą cechę w nowej linii',
    )

    class Meta:
        model = LessonType
        fields = [
            'name',
            'subtitle',
            'description',
            'icon_svg',
            'color',
            'order_index',
            'is_published',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'np. Zajęcia indywidualne',
            }),
            'subtitle': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'np. (do 4 osób)',
            }),
            'description': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 3,
                'placeholder': 'Opis formy zajęć...',
            }),
            'icon_svg': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full font-mono text-sm',
                'rows': 3,
                'placeholder': '<svg>...</svg>',
            }),
            'color': forms.Select(
                choices=[
                    ('brand', 'Brand (niebieski)'),
                    ('emerald', 'Emerald (zielony)'),
                ],
                attrs={'class': 'select select-bordered w-full'},
            ),
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
            self.fields['features_text'].initial = '\n'.join(self.instance.features or [])

    def save(self, commit=True):
        instance = super().save(commit=False)
        features_text = self.cleaned_data.get('features_text', '')
        instance.features = [
            line.strip() for line in features_text.split('\n') if line.strip()
        ]
        if commit:
            instance.save()
        return instance
