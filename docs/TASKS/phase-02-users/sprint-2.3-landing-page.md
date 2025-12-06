# Phase 2 - Sprint 2.3: Landing Page & Public Website (Django)

## Tasks 044A-044G: Public Website with Maps, Team, Testimonials

> **Duration**: Week 5, Days 1-3 (3 dni)
> **Goal**: Professional landing page with CMS-managed content
> **Dependencies**: Phase 2 Sprint 2.1-2.2 complete

---

## SPRINT OVERVIEW

| Task ID | Description                     | Priority | Dependencies |
| ------- | ------------------------------- | -------- | ------------ |
| 044A    | Django models for CMS           | Critical | Sprint 2.2   |
| 044B    | Landing page layout             | Critical | Task 044A    |
| 044C    | Hero section + CTA              | Critical | Task 044B    |
| 044D    | Team section with tutors        | High     | Task 044A    |
| 044E    | Testimonials carousel           | High     | Task 044A    |
| 044F    | Location map (Google Maps)      | High     | Task 044A    |
| 044G    | Additional sections (FAQ, etc.) | Medium   | Tasks 044B-F |

---

## CMS MODELS

**File**: `apps/landing/models.py`

```python
from django.db import models


class PageContent(models.Model):
    """CMS content for landing pages."""

    page_key = models.CharField('Klucz strony', max_length=50, unique=True)
    title = models.CharField('Tytuł', max_length=200)
    subtitle = models.CharField('Podtytuł', max_length=300, blank=True)
    content = models.TextField('Treść', blank=True)
    data = models.JSONField('Dane dodatkowe', default=dict, blank=True)
    is_active = models.BooleanField('Aktywna', default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'page_contents'
        verbose_name = 'Treść strony'
        verbose_name_plural = 'Treści stron'


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

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'testimonials'
        ordering = ['display_order']


class TeamMember(models.Model):
    """Public team member profiles."""

    user = models.OneToOneField(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    name = models.CharField('Imię', max_length=100)
    surname = models.CharField('Nazwisko', max_length=100)
    position = models.CharField('Stanowisko', max_length=100, blank=True)
    bio = models.TextField('Opis', blank=True)
    expertise = models.JSONField('Specjalizacje', default=list)
    image = models.ImageField('Zdjęcie', upload_to='team/', blank=True)
    order_index = models.PositiveIntegerField('Kolejność', default=0)
    is_published = models.BooleanField('Opublikowany', default=True)

    class Meta:
        db_table = 'team_members'
        ordering = ['order_index']


class FAQItem(models.Model):
    """FAQ items for landing page."""

    question = models.CharField('Pytanie', max_length=300)
    answer = models.TextField('Odpowiedź')
    category = models.CharField('Kategoria', max_length=50, blank=True)
    order_index = models.PositiveIntegerField('Kolejność', default=0)
    is_published = models.BooleanField('Opublikowane', default=True)

    class Meta:
        db_table = 'faq_items'
        ordering = ['order_index']


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
    latitude = models.DecimalField('Szerokość geo', max_digits=10, decimal_places=8, null=True)
    longitude = models.DecimalField('Długość geo', max_digits=11, decimal_places=8, null=True)
    opening_hours = models.JSONField('Godziny otwarcia', default=dict)
    social_media = models.JSONField('Social media', default=dict)

    class Meta:
        db_table = 'school_info'


class Lead(models.Model):
    """Contact form submissions."""

    STATUS_CHOICES = [
        ('new', 'Nowy'),
        ('contacted', 'Skontaktowany'),
        ('converted', 'Skonwertowany'),
        ('lost', 'Utracony'),
    ]

    name = models.CharField('Imię', max_length=100)
    email = models.EmailField('Email')
    phone = models.CharField('Telefon', max_length=20, blank=True)
    subject = models.CharField('Temat', max_length=200)
    message = models.TextField('Wiadomość')
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='new')
    gdpr_consent = models.BooleanField('Zgoda RODO', default=False)
    marketing_consent = models.BooleanField('Zgoda marketingowa', default=False)
    source = models.CharField('Źródło', max_length=50, default='website')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'leads'
        ordering = ['-created_at']
```

---

## LANDING PAGE VIEWS

**File**: `apps/landing/views.py`

```python
from django.views.generic import TemplateView, CreateView
from django.contrib import messages
from django.http import HttpResponse

from .models import PageContent, Testimonial, TeamMember, FAQItem, SchoolInfo, Lead
from .forms import ContactForm


class LandingPageView(TemplateView):
    """Main landing page."""

    template_name = 'landing/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update({
            'hero': PageContent.objects.filter(page_key='hero', is_active=True).first(),
            'about': PageContent.objects.filter(page_key='about', is_active=True).first(),
            'team': TeamMember.objects.filter(is_published=True),
            'testimonials': Testimonial.objects.filter(is_published=True),
            'faq_items': FAQItem.objects.filter(is_published=True),
            'school_info': SchoolInfo.objects.first(),
            'subjects': Subject.objects.filter(is_active=True),
            'contact_form': ContactForm(),
        })

        return context


class ContactFormView(CreateView):
    """Handle contact form submission with HTMX."""

    model = Lead
    form_class = ContactForm
    template_name = 'landing/partials/_contact_form.html'

    def form_valid(self, form):
        form.save()

        # Send notification email (Celery task)
        from .tasks import notify_new_lead
        notify_new_lead.delay(form.instance.id)

        if self.request.htmx:
            return HttpResponse('''
                <div class="alert alert-success">
                    <span>Dziękujemy za wiadomość! Skontaktujemy się wkrótce.</span>
                </div>
            ''')

        messages.success(self.request, 'Wiadomość została wysłana.')
        return redirect('landing:home')

    def form_invalid(self, form):
        if self.request.htmx:
            return render(self.request, self.template_name, {'form': form})
        return super().form_invalid(form)
```

---

## LANDING PAGE TEMPLATES

**File**: `templates/landing/index.html`

```html
{% extends "landing/base.html" %}

{% block content %}
<!-- Hero Section -->
<section class="hero min-h-screen bg-gradient-to-br from-primary to-secondary text-primary-content">
    <div class="hero-content text-center">
        <div class="max-w-3xl">
            <h1 class="text-5xl font-bold">{{ hero.title|default:"Korepetycje, które prowadzą do sukcesu" }}</h1>
            <p class="py-6 text-xl">{{ hero.subtitle|default:"Profesjonalni korepetytorzy, indywidualne podejście" }}</p>
            <div class="flex gap-4 justify-center">
                <a href="#kontakt" class="btn btn-accent btn-lg">Zapytaj o termin</a>
                <a href="#cennik" class="btn btn-outline btn-lg">Zobacz cennik</a>
            </div>
        </div>
    </div>
</section>

<!-- Team Section -->
<section id="zespol" class="py-20 bg-base-200">
    <div class="container mx-auto px-4">
        <h2 class="text-4xl font-bold text-center mb-12">Nasi Korepetytorzy</h2>
        <div class="grid md:grid-cols-3 gap-8">
            {% for member in team %}
            <div class="card bg-base-100 shadow-xl">
                <figure class="px-10 pt-10">
                    {% if member.image %}
                        <img src="{{ member.image.url }}" alt="{{ member.name }}" class="rounded-xl w-32 h-32 object-cover">
                    {% else %}
                        <div class="avatar placeholder">
                            <div class="bg-neutral text-neutral-content rounded-full w-32">
                                <span class="text-3xl">{{ member.name.0 }}{{ member.surname.0 }}</span>
                            </div>
                        </div>
                    {% endif %}
                </figure>
                <div class="card-body items-center text-center">
                    <h3 class="card-title">{{ member.name }} {{ member.surname }}</h3>
                    <p class="text-sm text-base-content/60">{{ member.position }}</p>
                    <div class="flex flex-wrap gap-2 mt-2">
                        {% for subject in member.expertise %}
                            <span class="badge badge-outline">{{ subject }}</span>
                        {% endfor %}
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
</section>

<!-- Testimonials Carousel -->
<section class="py-20">
    <div class="container mx-auto px-4">
        <h2 class="text-4xl font-bold text-center mb-12">Opinie rodziców i uczniów</h2>
        <div class="carousel w-full" x-data="{ current: 0 }">
            {% for testimonial in testimonials %}
            <div class="carousel-item w-full" :class="{ 'hidden': current !== {{ forloop.counter0 }} }">
                <div class="card bg-base-100 shadow-xl mx-auto max-w-2xl">
                    <div class="card-body">
                        <div class="rating mb-4">
                            {% for i in "12345" %}
                                <input type="radio" class="mask mask-star-2 bg-warning"
                                       {% if forloop.counter <= testimonial.rating %}checked{% endif %} disabled>
                            {% endfor %}
                        </div>
                        <blockquote class="text-lg italic">"{{ testimonial.content }}"</blockquote>
                        <p class="font-semibold mt-4">— {{ testimonial.student_name }}</p>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
        <div class="flex justify-center gap-2 mt-4">
            {% for testimonial in testimonials %}
                <button class="btn btn-xs" @click="current = {{ forloop.counter0 }}">{{ forloop.counter }}</button>
            {% endfor %}
        </div>
    </div>
</section>

<!-- FAQ Section -->
<section id="faq" class="py-20 bg-base-200">
    <div class="container mx-auto px-4 max-w-3xl">
        <h2 class="text-4xl font-bold text-center mb-12">Często zadawane pytania</h2>
        <div class="space-y-4">
            {% for item in faq_items %}
            <div class="collapse collapse-arrow bg-base-100">
                <input type="radio" name="faq-accordion" {% if forloop.first %}checked{% endif %}>
                <div class="collapse-title text-xl font-medium">{{ item.question }}</div>
                <div class="collapse-content">
                    <p>{{ item.answer }}</p>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
</section>

<!-- Contact Section -->
<section id="kontakt" class="py-20">
    <div class="container mx-auto px-4">
        <div class="grid lg:grid-cols-2 gap-12">
            <!-- Contact Form -->
            <div class="card bg-base-100 shadow-xl">
                <div class="card-body">
                    <h3 class="card-title text-2xl mb-4">Wyślij wiadomość</h3>
                    <div id="contact-form-container">
                        {% include "landing/partials/_contact_form.html" %}
                    </div>
                </div>
            </div>

            <!-- Map & Contact Info -->
            <div class="space-y-6">
                <div class="card bg-base-100 shadow-xl">
                    <div class="card-body">
                        <h4 class="font-semibold">Adres</h4>
                        <p>{{ school_info.address }}, {{ school_info.city }}</p>
                    </div>
                </div>
                <div class="card bg-base-100 shadow-xl">
                    <div class="card-body">
                        <h4 class="font-semibold">Telefon</h4>
                        <p>{{ school_info.phone }}</p>
                    </div>
                </div>
                <div class="card bg-base-100 shadow-xl">
                    <div class="card-body">
                        <h4 class="font-semibold">Email</h4>
                        <p>{{ school_info.email }}</p>
                    </div>
                </div>
                <!-- Google Map -->
                {% if school_info.latitude and school_info.longitude %}
                <div id="map" class="w-full h-64 rounded-lg"
                     data-lat="{{ school_info.latitude }}"
                     data-lng="{{ school_info.longitude }}">
                </div>
                {% endif %}
            </div>
        </div>
    </div>
</section>
{% endblock %}
```

---

## CONTACT FORM

**File**: `apps/landing/forms.py`

```python
from django import forms
from .models import Lead


class ContactForm(forms.ModelForm):
    """Contact form with GDPR consent."""

    gdpr_consent = forms.BooleanField(
        label='Wyrażam zgodę na przetwarzanie danych osobowych',
        required=True,
    )

    class Meta:
        model = Lead
        fields = ['name', 'email', 'phone', 'subject', 'message', 'gdpr_consent', 'marketing_consent']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input input-bordered w-full', 'placeholder': 'Imię i nazwisko'}),
            'email': forms.EmailInput(attrs={'class': 'input input-bordered w-full', 'placeholder': 'Email'}),
            'phone': forms.TextInput(attrs={'class': 'input input-bordered w-full', 'placeholder': 'Telefon'}),
            'subject': forms.TextInput(attrs={'class': 'input input-bordered w-full', 'placeholder': 'Temat'}),
            'message': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full', 'rows': 4}),
        }
```

---

## URL CONFIGURATION

**File**: `apps/landing/urls.py`

```python
from django.urls import path
from . import views

app_name = 'landing'

urlpatterns = [
    path('', views.LandingPageView.as_view(), name='home'),
    path('kontakt/', views.ContactFormView.as_view(), name='contact'),
]
```

---

## COMPLETION CHECKLIST

- [ ] CMS models created and migrated
- [ ] Landing page renders all sections
- [ ] Team members display correctly
- [ ] Testimonials carousel works
- [ ] FAQ accordion functional
- [ ] Contact form submits via HTMX
- [ ] Lead saved to database
- [ ] Google Map displays (if configured)
- [ ] Mobile responsive design

---

**Sprint Completion**: All 7 tasks completed
**Next Sprint**: 2.4 - CMS Admin Panel
