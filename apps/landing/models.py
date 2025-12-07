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
    email = models.EmailField('Email', blank=True)
    phone = models.CharField('Telefon', max_length=20, blank=True)
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
