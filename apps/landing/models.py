from django.db import models

from apps.core.models import TimeStampedModel


class PageContent(TimeStampedModel):
    """CMS content for landing pages."""

    page_key = models.CharField('Klucz strony', max_length=50, unique=True)
    title = models.CharField('Tytuł', max_length=200)
    subtitle = models.CharField('Podtytuł', max_length=300, blank=True)
    content = models.TextField('Treść', blank=True)
    data = models.JSONField('Dane dodatkowe', default=dict, blank=True)
    is_active = models.BooleanField('Aktywna', default=True)

    class Meta:
        db_table = 'page_contents'
        verbose_name = 'Treść strony'
        verbose_name_plural = 'Treści stron'

    def __str__(self) -> str:
        return f'{self.page_key}: {self.title}'


class Testimonial(models.Model):
    """Student/parent testimonials."""

    student_name = models.CharField('Imię ucznia', max_length=100)
    parent_name = models.CharField('Imię rodzica', max_length=100, blank=True)
    content = models.TextField('Treść opinii')
    rating = models.PositiveIntegerField('Ocena', default=5)
    subject = models.CharField('Przedmiot', max_length=50, blank=True)
    level = models.CharField('Poziom', max_length=50, blank=True)
    image = models.ImageField('Zdjęcie', upload_to='testimonials/', blank=True)
    is_verified = models.BooleanField('Zweryfikowana', default=False)
    is_published = models.BooleanField('Opublikowana', default=False)
    display_order = models.PositiveIntegerField('Kolejność', default=0)

    created_at = models.DateTimeField('Utworzono', auto_now_add=True)

    class Meta:
        db_table = 'testimonials'
        verbose_name = 'Opinia'
        verbose_name_plural = 'Opinie'
        ordering = ['display_order']

    def __str__(self) -> str:
        return f'{self.student_name} - {self.subject}'


class TeamMember(models.Model):
    """Public team member profiles."""

    user = models.OneToOneField(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Użytkownik',
    )
    name = models.CharField('Imię', max_length=100)
    surname = models.CharField('Nazwisko', max_length=100)
    position = models.CharField('Stanowisko', max_length=100, blank=True)
    bio = models.TextField('Opis', blank=True)
    expertise = models.JSONField('Specjalizacje', default=list, blank=True)
    image = models.ImageField('Zdjęcie', upload_to='team/', blank=True)
    order_index = models.PositiveIntegerField('Kolejność', default=0)
    is_published = models.BooleanField('Opublikowany', default=True)

    class Meta:
        db_table = 'team_members'
        verbose_name = 'Członek zespołu'
        verbose_name_plural = 'Członkowie zespołu'
        ordering = ['order_index']

    def __str__(self) -> str:
        return f'{self.name} {self.surname}'


class FAQItem(models.Model):
    """FAQ items for landing page."""

    question = models.CharField('Pytanie', max_length=300)
    answer = models.TextField('Odpowiedź')
    category = models.CharField('Kategoria', max_length=50, blank=True)
    order_index = models.PositiveIntegerField('Kolejność', default=0)
    is_published = models.BooleanField('Opublikowane', default=True)

    class Meta:
        db_table = 'faq_items'
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQ'
        ordering = ['order_index']

    def __str__(self) -> str:
        return self.question[:50]


class SchoolInfo(models.Model):
    """School contact and info settings."""

    name = models.CharField('Nazwa', max_length=100, default='Na Piątkę')
    tagline = models.CharField('Slogan', max_length=200, blank=True)
    description = models.TextField('Opis', blank=True)
    logo = models.ImageField('Logo', upload_to='school/', blank=True)
    logo_dark = models.ImageField('Logo (ciemne tło)', upload_to='school/', blank=True)
    favicon = models.ImageField('Favicon', upload_to='school/', blank=True)
    email = models.EmailField('Email', blank=True)
    phone = models.CharField('Telefon', max_length=20, blank=True)
    phone_secondary = models.CharField('Telefon dodatkowy', max_length=20, blank=True)
    address = models.CharField('Adres', max_length=200, blank=True)
    city = models.CharField('Miasto', max_length=100, blank=True)
    postal_code = models.CharField('Kod pocztowy', max_length=10, blank=True)
    latitude = models.DecimalField(
        'Szerokość geo',
        max_digits=10,
        decimal_places=8,
        null=True,
        blank=True,
    )
    longitude = models.DecimalField(
        'Długość geo',
        max_digits=11,
        decimal_places=8,
        null=True,
        blank=True,
    )
    opening_hours = models.JSONField('Godziny otwarcia', default=dict, blank=True)
    social_media = models.JSONField('Social media', default=dict, blank=True)
    footer_text = models.TextField('Tekst stopki', blank=True)
    copyright_text = models.CharField('Tekst copyright', max_length=200, blank=True)

    class Meta:
        db_table = 'school_info'
        verbose_name = 'Informacje o szkole'
        verbose_name_plural = 'Informacje o szkole'

    def __str__(self) -> str:
        return self.name


class Lead(models.Model):
    """Contact form submissions."""

    class Status(models.TextChoices):
        NEW = 'new', 'Nowy'
        CONTACTED = 'contacted', 'Skontaktowany'
        CONVERTED = 'converted', 'Skonwertowany'
        LOST = 'lost', 'Utracony'

    name = models.CharField('Imię', max_length=100)
    email = models.EmailField('Email')
    phone = models.CharField('Telefon', max_length=20, blank=True)
    subject = models.CharField('Temat', max_length=200)
    message = models.TextField('Wiadomość')
    status = models.CharField(
        'Status',
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
    )
    gdpr_consent = models.BooleanField('Zgoda RODO', default=False)
    marketing_consent = models.BooleanField('Zgoda marketingowa', default=False)
    source = models.CharField('Źródło', max_length=50, default='website')

    created_at = models.DateTimeField('Utworzono', auto_now_add=True)

    class Meta:
        db_table = 'leads'
        verbose_name = 'Lead'
        verbose_name_plural = 'Leady'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.name} - {self.subject}'


class LandingStatistic(models.Model):
    """Editable statistics for landing page (e.g., '5+ lat', '100+ uczniów')."""

    label = models.CharField('Etykieta', max_length=100)
    value = models.CharField('Wartość', max_length=50)
    description = models.CharField('Opis', max_length=200, blank=True)
    icon = models.CharField('Ikona (SVG lub klasa)', max_length=100, blank=True)
    order_index = models.PositiveIntegerField('Kolejność', default=0)
    is_published = models.BooleanField('Opublikowane', default=True)

    class Meta:
        db_table = 'landing_statistics'
        verbose_name = 'Statystyka'
        verbose_name_plural = 'Statystyki'
        ordering = ['order_index']

    def __str__(self) -> str:
        return f'{self.value} - {self.label}'


class WhyUsCard(models.Model):
    """Editable 'Why Us' cards for landing page."""

    title = models.CharField('Tytuł', max_length=100)
    description = models.TextField('Opis')
    icon = models.TextField('Ikona SVG', blank=True)
    color = models.CharField(
        'Kolor',
        max_length=50,
        default='brand',
        help_text='Nazwa koloru: brand, emerald, blue, purple, orange, teal',
    )
    link = models.CharField('Link (opcjonalnie)', max_length=200, blank=True)
    order_index = models.PositiveIntegerField('Kolejność', default=0)
    is_published = models.BooleanField('Opublikowane', default=True)

    class Meta:
        db_table = 'why_us_cards'
        verbose_name = 'Karta "Dlaczego my"'
        verbose_name_plural = 'Karty "Dlaczego my"'
        ordering = ['order_index']

    def __str__(self) -> str:
        return self.title


class LandingSubject(models.Model):
    """Editable subjects for landing page."""

    name = models.CharField('Nazwa', max_length=100)
    slug = models.SlugField('Slug', unique=True)
    short_description = models.TextField('Krótki opis')
    full_description = models.TextField('Pełny opis', blank=True)
    icon_svg = models.TextField('Ikona SVG')
    color_from = models.CharField(
        'Kolor gradient (od)',
        max_length=50,
        default='blue-500',
        help_text='np. blue-500, emerald-500, amber-500',
    )
    color_to = models.CharField(
        'Kolor gradient (do)',
        max_length=50,
        default='indigo-600',
        help_text='np. indigo-600, teal-600, orange-600',
    )
    levels = models.CharField(
        'Poziomy',
        max_length=100,
        default='Wszystkie poziomy',
        help_text='np. "A1 - C2" lub "Wszystkie poziomy"',
    )
    topics = models.JSONField(
        'Tematy',
        default=list,
        blank=True,
        help_text='Lista tematów do wyświetlenia w modalu',
    )
    target_groups = models.JSONField(
        'Grupy docelowe',
        default=list,
        blank=True,
        help_text='Lista grup docelowych',
    )
    order_index = models.PositiveIntegerField('Kolejność', default=0)
    is_published = models.BooleanField('Opublikowany', default=True)
    is_featured = models.BooleanField(
        'Wyróżniony',
        default=False,
        help_text='Wyróżnione przedmioty zajmują więcej miejsca',
    )

    class Meta:
        db_table = 'landing_subjects'
        verbose_name = 'Przedmiot (landing)'
        verbose_name_plural = 'Przedmioty (landing)'
        ordering = ['order_index']

    def __str__(self) -> str:
        return self.name


class PricingPackage(models.Model):
    """Editable pricing packages for landing page."""

    name = models.CharField('Nazwa', max_length=100)
    sessions_count = models.PositiveIntegerField('Liczba spotkań')
    individual_price = models.DecimalField(
        'Cena indywidualna (od)',
        max_digits=10,
        decimal_places=2,
    )
    group_price = models.DecimalField(
        'Cena grupowa (od)',
        max_digits=10,
        decimal_places=2,
    )
    is_popular = models.BooleanField('Najpopularniejszy', default=False)
    order_index = models.PositiveIntegerField('Kolejność', default=0)
    is_published = models.BooleanField('Opublikowany', default=True)

    class Meta:
        db_table = 'pricing_packages'
        verbose_name = 'Pakiet cenowy'
        verbose_name_plural = 'Pakiety cenowe'
        ordering = ['order_index']

    def __str__(self) -> str:
        return f'{self.name} ({self.sessions_count} spotkań)'


class EducationLevel(models.Model):
    """Editable education levels for landing page."""

    name = models.CharField('Nazwa', max_length=100)
    icon_svg = models.TextField('Ikona SVG', blank=True)
    color = models.CharField(
        'Kolor',
        max_length=50,
        default='brand',
        help_text='np. brand, emerald, blue, red',
    )
    order_index = models.PositiveIntegerField('Kolejność', default=0)
    is_published = models.BooleanField('Opublikowany', default=True)

    class Meta:
        db_table = 'education_levels'
        verbose_name = 'Poziom edukacyjny'
        verbose_name_plural = 'Poziomy edukacyjne'
        ordering = ['order_index']

    def __str__(self) -> str:
        return self.name


class LessonType(models.Model):
    """Editable lesson types (individual, group) for landing page."""

    name = models.CharField('Nazwa', max_length=100)
    subtitle = models.CharField('Podtytuł', max_length=200, blank=True)
    description = models.TextField('Opis')
    icon_svg = models.TextField('Ikona SVG')
    color = models.CharField('Kolor', max_length=50, default='brand')
    features = models.JSONField(
        'Cechy',
        default=list,
        help_text='Lista cech/zalet tej formy zajęć',
    )
    order_index = models.PositiveIntegerField('Kolejność', default=0)
    is_published = models.BooleanField('Opublikowany', default=True)

    class Meta:
        db_table = 'lesson_types'
        verbose_name = 'Forma zajęć'
        verbose_name_plural = 'Formy zajęć'
        ordering = ['order_index']

    def __str__(self) -> str:
        return self.name
