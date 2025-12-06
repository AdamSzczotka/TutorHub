# Implementation Guidelines & Best Practices

## System "Na Piątkę" - Sztywne Zasady Implementacji (Django + HTMX)

> **CRITICAL**: Ten dokument jest OBOWIĄZKOWY dla wszystkich developerów.
> Każda linia kodu MUSI być zgodna z tymi wytycznymi.
> Nieprzestrzeganie = odrzucenie PR.
> Data utworzenia: Grudzień 2025
> **Stack**: Django 5.1 + HTMX + Alpine.js + Tailwind CSS

---

## 1. STRUKTURA PROJEKTU

### 1.1 Organizacja Folderów

```
napiatke/
├── manage.py                     # Django CLI entry point
├── napiatke/                     # Główny projekt Django
│   ├── __init__.py
│   ├── settings/                 # Podzielone ustawienia
│   │   ├── __init__.py
│   │   ├── base.py              # Wspólne ustawienia
│   │   ├── development.py       # Development settings
│   │   └── production.py        # Production settings
│   ├── urls.py                   # Główny URL routing
│   ├── wsgi.py                   # WSGI entry point
│   ├── asgi.py                   # ASGI entry point
│   └── celery.py                 # Celery configuration
│
├── apps/                         # Django applications
│   ├── core/                     # Wspólne utilities
│   │   ├── __init__.py
│   │   ├── models.py            # Base models (TimeStampedModel)
│   │   ├── mixins.py            # View mixins (HTMXMixin, etc.)
│   │   ├── utils.py             # Helper functions
│   │   ├── context_processors.py
│   │   └── templatetags/        # Custom template tags
│   │       └── core_tags.py
│   │
│   ├── accounts/                 # Auth & User management
│   │   ├── __init__.py
│   │   ├── models.py            # Custom User model
│   │   ├── views.py             # Auth views
│   │   ├── forms.py             # Login, registration forms
│   │   ├── urls.py
│   │   ├── admin.py
│   │   ├── managers.py          # Custom user manager
│   │   └── signals.py           # User signals
│   │
│   ├── tutors/                   # Tutor profiles & management
│   ├── students/                 # Student profiles & management
│   ├── lessons/                  # Lessons & Calendar
│   ├── rooms/                    # Room management
│   ├── subjects/                 # Subjects & Levels
│   ├── attendance/               # Attendance tracking
│   ├── cancellations/            # Cancellation & makeup lessons
│   ├── invoices/                 # Billing & invoicing
│   ├── messages/                 # Internal messaging
│   ├── notifications/            # Notification system
│   ├── reports/                  # Reports & statistics
│   └── landing/                  # Public landing page
│
├── templates/                    # Django Templates
│   ├── base.html                # Base template
│   ├── components/               # Reusable UI components
│   │   ├── _button.html
│   │   ├── _modal.html
│   │   ├── _table.html
│   │   ├── _card.html
│   │   ├── _form_field.html
│   │   ├── _pagination.html
│   │   ├── _alert.html
│   │   ├── _dropdown.html
│   │   └── _loading.html
│   │
│   ├── layouts/                  # Layout templates per role
│   │   ├── _admin_sidebar.html
│   │   ├── _tutor_nav.html
│   │   ├── _student_nav.html
│   │   ├── admin.html
│   │   ├── tutor.html
│   │   └── student.html
│   │
│   ├── partials/                 # HTMX partial responses
│   │   ├── accounts/
│   │   ├── lessons/
│   │   ├── users/
│   │   └── ...
│   │
│   ├── emails/                   # Email templates
│   │   ├── base_email.html
│   │   ├── welcome.html
│   │   └── password_reset.html
│   │
│   └── errors/                   # Error pages
│       ├── 400.html
│       ├── 403.html
│       ├── 404.html
│       └── 500.html
│
├── static/                       # Static files
│   ├── css/
│   │   ├── input.css            # Tailwind input
│   │   └── output.css           # Compiled Tailwind
│   ├── js/
│   │   ├── htmx.min.js          # HTMX library
│   │   ├── alpine.min.js        # Alpine.js
│   │   └── app.js               # Custom scripts
│   └── img/
│       ├── logo.svg
│       └── ...
│
├── media/                        # User uploaded files
│
├── tests/                        # Test directory
│   ├── conftest.py              # pytest fixtures
│   ├── factories.py             # Factory Boy factories
│   ├── accounts/
│   ├── lessons/
│   └── ...
│
├── docker/
│   ├── Dockerfile
│   ├── Dockerfile.prod
│   └── nginx.conf
│
├── docker-compose.yml
├── docker-compose.prod.yml
├── requirements/
│   ├── base.txt
│   ├── development.txt
│   └── production.txt
├── pyproject.toml                # Ruff, mypy, pytest config
├── .pre-commit-config.yaml
├── .env.example
└── README.md
```

### 1.2 Konwencje Nazewnictwa

#### Pliki i Foldery Python

```python
# Moduły Python - snake_case
user_management.py
invoice_service.py
attendance_views.py

# Django Apps - snake_case (singular lub plural)
accounts/
lessons/
invoices/

# Templates - snake_case z prefiksem _ dla partials
user_list.html       # Pełna strona
_user_card.html      # Partial/component
_user_row.html       # HTMX partial response
```

#### Klasy i Funkcje

```python
# Klasy - PascalCase
class UserProfile(models.Model):
    pass

class LessonListView(ListView):
    pass

class CreateUserForm(forms.ModelForm):
    pass

# Funkcje - snake_case
def calculate_invoice_total():
    pass

def get_user_by_email():
    pass

# Widoki funkcyjne - snake_case
def user_list(request):
    pass

def lesson_detail(request, pk):
    pass

# Zmienne - snake_case
user_name = "John"
is_authenticated = True
total_lessons = 10

# Stałe - UPPER_SNAKE_CASE
MAX_RETRY_COUNT = 3
DEFAULT_PAGE_SIZE = 20
LESSON_DURATION_MINUTES = 60
```

#### Models

```python
# Model name - singular PascalCase
class User(AbstractUser):
    pass

class Lesson(models.Model):
    pass

class Invoice(models.Model):
    pass

# Related names - plural snake_case
class Lesson(models.Model):
    tutor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='lessons_as_tutor'  # Plural!
    )
    students = models.ManyToManyField(
        User,
        related_name='lessons_as_student'
    )

# Choice fields - jako klasy
class UserRole(models.TextChoices):
    ADMIN = 'admin', 'Administrator'
    TUTOR = 'tutor', 'Korepetytor'
    STUDENT = 'student', 'Uczeń'
```

---

## 2. CODING STANDARDS

### 2.1 Python/Django Configuration

**pyproject.toml MUST have:**

```toml
[tool.ruff]
target-version = "py312"
line-length = 88
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # Pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
    "DJ",  # flake8-django
]
ignore = [
    "E501",  # line too long (handled by formatter)
]

[tool.ruff.isort]
known-first-party = ["apps", "napiatke"]

[tool.mypy]
python_version = "3.12"
plugins = ["mypy_django_plugin.main"]
strict = true
ignore_missing_imports = true

[tool.django-stubs]
django_settings_module = "napiatke.settings.development"

[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "napiatke.settings.development"
python_files = ["test_*.py"]
addopts = "-v --tb=short"
```

### 2.2 Import Order

**ZAWSZE w tej kolejności (Ruff wymusza automatycznie):**

```python
# 1. Standard library
import os
from datetime import datetime, timedelta
from typing import Any

# 2. Third-party packages
from celery import shared_task
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView, DetailView

# 3. Local app imports
from apps.core.mixins import HTMXMixin
from apps.accounts.models import User

# 4. Relative imports (tylko wewnątrz tej samej app)
from .forms import CreateUserForm
from .models import TutorProfile
```

### 2.3 Docstrings & Type Hints

```python
from typing import Optional
from django.http import HttpRequest, HttpResponse

def create_lesson(
    request: HttpRequest,
    tutor_id: int,
    *,
    subject_id: Optional[int] = None,
) -> HttpResponse:
    """
    Tworzy nową lekcję dla korepetytora.

    Args:
        request: Django HTTP request object
        tutor_id: ID korepetytora
        subject_id: Opcjonalny ID przedmiotu

    Returns:
        HttpResponse z przekierowaniem lub formularzem

    Raises:
        Http404: Gdy korepetytor nie istnieje
        PermissionDenied: Gdy użytkownik nie ma uprawnień
    """
    tutor = get_object_or_404(User, pk=tutor_id, role='tutor')
    # ... implementacja
```

---

## 3. DJANGO BEST PRACTICES

### 3.1 Models

```python
# apps/core/models.py
from django.db import models
import uuid


class TimeStampedModel(models.Model):
    """Abstract base model z timestamps."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# apps/accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from apps.core.models import TimeStampedModel


class User(AbstractUser, TimeStampedModel):
    """Custom User model z rolami."""

    class Role(models.TextChoices):
        ADMIN = 'admin', 'Administrator'
        TUTOR = 'tutor', 'Korepetytor'
        STUDENT = 'student', 'Uczeń'

    # Override id from TimeStampedModel
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
    )
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
    )
    first_login = models.BooleanField(default=True)
    is_profile_completed = models.BooleanField(default=False)

    class Meta:
        db_table = 'users'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"{self.get_full_name()} ({self.role})"

    @property
    def is_admin(self) -> bool:
        return self.role == self.Role.ADMIN

    @property
    def is_tutor(self) -> bool:
        return self.role == self.Role.TUTOR

    @property
    def is_student(self) -> bool:
        return self.role == self.Role.STUDENT
```

### 3.2 Views - Class-Based Views (preferowane)

```python
# apps/lessons/views.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.http import HttpResponse

from apps.core.mixins import HTMXMixin, AdminRequiredMixin
from .models import Lesson
from .forms import LessonForm


class LessonListView(LoginRequiredMixin, HTMXMixin, ListView):
    """Lista lekcji z obsługą HTMX."""

    model = Lesson
    template_name = 'lessons/lesson_list.html'
    partial_template_name = 'partials/lessons/_lesson_list.html'
    context_object_name = 'lessons'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filtrowanie
        if self.request.GET.get('tutor'):
            queryset = queryset.filter(tutor_id=self.request.GET['tutor'])

        if self.request.GET.get('search'):
            queryset = queryset.filter(
                title__icontains=self.request.GET['search']
            )

        return queryset.select_related('tutor', 'room', 'subject')


class LessonCreateView(AdminRequiredMixin, HTMXMixin, CreateView):
    """Tworzenie nowej lekcji."""

    model = Lesson
    form_class = LessonForm
    template_name = 'lessons/lesson_form.html'
    success_url = reverse_lazy('lessons:list')

    def form_valid(self, form):
        response = super().form_valid(form)

        if self.request.htmx:
            # Zwróć partial z nową lekcją
            return render(
                self.request,
                'partials/lessons/_lesson_row.html',
                {'lesson': self.object}
            )

        return response
```

### 3.3 Views - Function-Based (dla prostych przypadków)

```python
# apps/accounts/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpRequest, HttpResponse

from .models import User
from .forms import UserProfileForm


@login_required
def profile_view(request: HttpRequest) -> HttpResponse:
    """Widok profilu użytkownika."""

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()

            if request.htmx:
                return render(
                    request,
                    'partials/accounts/_profile_success.html',
                    {'message': 'Profil zaktualizowany!'}
                )

            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=request.user)

    template = 'accounts/profile.html'
    if request.htmx:
        template = 'partials/accounts/_profile_form.html'

    return render(request, template, {'form': form})
```

### 3.4 HTMX Mixin

```python
# apps/core/mixins.py
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpResponse


class HTMXMixin:
    """Mixin do obsługi requestów HTMX."""

    partial_template_name: str = None

    def get_template_names(self):
        if self.request.htmx and self.partial_template_name:
            return [self.partial_template_name]
        return super().get_template_names()

    def render_to_response(self, context, **response_kwargs):
        response = super().render_to_response(context, **response_kwargs)

        # Dodaj HTMX headers jeśli potrzebne
        if self.request.htmx:
            # Opcjonalnie: trigger events
            # response['HX-Trigger'] = 'lessonCreated'
            pass

        return response


class AdminRequiredMixin(UserPassesTestMixin):
    """Wymaga roli administratora."""

    def test_func(self) -> bool:
        return self.request.user.is_authenticated and self.request.user.is_admin


class TutorRequiredMixin(UserPassesTestMixin):
    """Wymaga roli korepetytora."""

    def test_func(self) -> bool:
        user = self.request.user
        return user.is_authenticated and (user.is_tutor or user.is_admin)


class StudentRequiredMixin(UserPassesTestMixin):
    """Wymaga roli ucznia."""

    def test_func(self) -> bool:
        user = self.request.user
        return user.is_authenticated and (user.is_student or user.is_admin)
```

---

## 4. FORMS BEST PRACTICES

### 4.1 ModelForms

```python
# apps/accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

from .models import User


class CreateUserForm(forms.ModelForm):
    """Formularz tworzenia użytkownika przez admina."""

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'phone', 'role']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'email@example.com',
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Imię',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Nazwisko',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': '+48 123 456 789',
            }),
            'role': forms.Select(attrs={
                'class': 'select select-bordered w-full',
            }),
        }

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email=email).exists():
            raise ValidationError('Użytkownik z tym emailem już istnieje.')
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '')
        # Usuń spacje i myślniki
        phone = ''.join(filter(str.isdigit, phone))
        if phone and len(phone) < 9:
            raise ValidationError('Numer telefonu musi mieć min. 9 cyfr.')
        return phone


class UserProfileForm(forms.ModelForm):
    """Formularz edycji profilu."""

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone', 'avatar']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dodaj Tailwind/daisyUI klasy
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'input input-bordered w-full'
```

### 4.2 Crispy Forms z Tailwind

```python
# apps/accounts/forms.py
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Submit, Div, HTML


class LoginForm(forms.Form):
    """Formularz logowania z Crispy Forms."""

    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    remember_me = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('email', css_class='input input-bordered w-full'),
            Field('password', css_class='input input-bordered w-full'),
            Div(
                Field('remember_me', css_class='checkbox'),
                HTML('<span class="label-text ml-2">Zapamiętaj mnie</span>'),
                css_class='form-control flex items-center gap-2 my-4'
            ),
            Submit('submit', 'Zaloguj się', css_class='btn btn-primary w-full'),
        )
```

---

## 5. URL PATTERNS

### 5.1 Główne URL

```python
# napiatke/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Django Admin
    path('django-admin/', admin.site.urls),

    # Public
    path('', include('apps.landing.urls')),

    # Auth
    path('auth/', include('apps.accounts.urls')),

    # Admin Panel
    path('admin/', include('apps.admin_panel.urls', namespace='admin_panel')),

    # Tutor Panel
    path('tutor/', include('apps.tutor_panel.urls', namespace='tutor_panel')),

    # Student Panel
    path('student/', include('apps.student_panel.urls', namespace='student_panel')),

    # API endpoints (dla HTMX)
    path('api/', include([
        path('lessons/', include('apps.lessons.api_urls')),
        path('users/', include('apps.accounts.api_urls')),
        path('notifications/', include('apps.notifications.api_urls')),
    ])),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    # Debug toolbar
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
```

### 5.2 App URLs

```python
# apps/lessons/urls.py
from django.urls import path
from . import views

app_name = 'lessons'

urlpatterns = [
    path('', views.LessonListView.as_view(), name='list'),
    path('create/', views.LessonCreateView.as_view(), name='create'),
    path('<uuid:pk>/', views.LessonDetailView.as_view(), name='detail'),
    path('<uuid:pk>/edit/', views.LessonUpdateView.as_view(), name='edit'),
    path('<uuid:pk>/delete/', views.LessonDeleteView.as_view(), name='delete'),

    # Calendar endpoints
    path('calendar/', views.calendar_view, name='calendar'),
    path('calendar/events/', views.calendar_events, name='calendar_events'),
]
```

---

## 6. TEMPLATES & HTMX

### 6.1 Base Template

```html
<!-- templates/base.html -->
<!DOCTYPE html>
<html lang="pl" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Na Piątkę{% endblock %}</title>

    <!-- Tailwind CSS -->
    <link href="{% static 'css/output.css' %}" rel="stylesheet">

    <!-- HTMX -->
    <script src="{% static 'js/htmx.min.js' %}" defer></script>

    <!-- Alpine.js -->
    <script src="{% static 'js/alpine.min.js' %}" defer></script>

    {% block extra_head %}{% endblock %}
</head>
<body class="min-h-screen bg-base-200"
      hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'>

    {% block body %}
    <main>
        {% block content %}{% endblock %}
    </main>
    {% endblock %}

    <!-- Toast notifications -->
    <div id="toast-container" class="toast toast-end"></div>

    {% block extra_js %}{% endblock %}
</body>
</html>
```

### 6.2 Layout Template (Admin)

```html
<!-- templates/layouts/admin.html -->
{% extends 'base.html' %}
{% load static %}

{% block body %}
<div class="drawer lg:drawer-open">
    <input id="admin-drawer" type="checkbox" class="drawer-toggle">

    <!-- Main content -->
    <div class="drawer-content flex flex-col">
        <!-- Navbar -->
        <nav class="navbar bg-base-100 shadow-lg lg:hidden">
            <label for="admin-drawer" class="btn btn-ghost drawer-button">
                <svg><!-- hamburger icon --></svg>
            </label>
            <span class="text-xl font-bold">Na Piątkę</span>
        </nav>

        <!-- Page content -->
        <main class="flex-1 p-6">
            {% block content %}{% endblock %}
        </main>
    </div>

    <!-- Sidebar -->
    <div class="drawer-side">
        <label for="admin-drawer" class="drawer-overlay"></label>
        {% include 'layouts/_admin_sidebar.html' %}
    </div>
</div>
{% endblock %}
```

### 6.3 HTMX Patterns

```html
<!-- Wyszukiwanie z debounce -->
<input type="search"
       name="search"
       placeholder="Szukaj użytkowników..."
       class="input input-bordered w-full"
       hx-get="{% url 'users:list' %}"
       hx-trigger="keyup changed delay:300ms"
       hx-target="#user-list"
       hx-swap="innerHTML"
       hx-indicator="#search-spinner">

<span id="search-spinner" class="htmx-indicator loading loading-spinner"></span>

<!-- Lista użytkowników -->
<div id="user-list">
    {% include 'partials/users/_user_list.html' %}
</div>
```

```html
<!-- Modal z formularzem -->
<button class="btn btn-primary"
        hx-get="{% url 'users:create' %}"
        hx-target="#modal-content"
        hx-swap="innerHTML"
        onclick="modal.showModal()">
    Dodaj użytkownika
</button>

<dialog id="modal" class="modal">
    <div class="modal-box">
        <div id="modal-content">
            <!-- Formularz zostanie załadowany przez HTMX -->
        </div>
    </div>
    <form method="dialog" class="modal-backdrop">
        <button>close</button>
    </form>
</dialog>
```

```html
<!-- Delete z potwierdzeniem -->
<button class="btn btn-error btn-sm"
        hx-delete="{% url 'users:delete' user.pk %}"
        hx-confirm="Czy na pewno chcesz usunąć użytkownika {{ user.get_full_name }}?"
        hx-target="closest tr"
        hx-swap="outerHTML swap:1s">
    Usuń
</button>
```

### 6.4 Partials dla HTMX

```html
<!-- templates/partials/users/_user_row.html -->
<tr id="user-{{ user.pk }}">
    <td>
        <div class="flex items-center gap-3">
            <div class="avatar">
                <div class="mask mask-squircle w-12 h-12">
                    {% if user.avatar %}
                        <img src="{{ user.avatar.url }}" alt="{{ user.get_full_name }}">
                    {% else %}
                        <div class="bg-neutral text-neutral-content flex items-center justify-center">
                            {{ user.first_name.0 }}{{ user.last_name.0 }}
                        </div>
                    {% endif %}
                </div>
            </div>
            <div>
                <div class="font-bold">{{ user.get_full_name }}</div>
                <div class="text-sm opacity-50">{{ user.email }}</div>
            </div>
        </div>
    </td>
    <td>
        <span class="badge badge-{{ user.role }}">{{ user.get_role_display }}</span>
    </td>
    <td>{{ user.last_login|date:"d.m.Y H:i"|default:"Nigdy" }}</td>
    <td>
        <div class="flex gap-2">
            <button class="btn btn-ghost btn-sm"
                    hx-get="{% url 'users:edit' user.pk %}"
                    hx-target="#modal-content"
                    onclick="modal.showModal()">
                Edytuj
            </button>
            <button class="btn btn-error btn-sm"
                    hx-delete="{% url 'users:delete' user.pk %}"
                    hx-confirm="Usunąć {{ user.get_full_name }}?"
                    hx-target="closest tr"
                    hx-swap="outerHTML">
                Usuń
            </button>
        </div>
    </td>
</tr>
```

---

## 7. ALPINE.JS PATTERNS

### 7.1 Component State

```html
<!-- Dropdown menu -->
<div x-data="{ open: false }" class="relative">
    <button @click="open = !open" class="btn">
        Menu
        <svg x-bind:class="{ 'rotate-180': open }" class="w-4 h-4 transition-transform">
            <!-- arrow icon -->
        </svg>
    </button>

    <div x-show="open"
         x-transition
         @click.away="open = false"
         class="absolute right-0 mt-2 w-48 bg-base-100 rounded-lg shadow-lg">
        <ul class="menu">
            <li><a href="#">Opcja 1</a></li>
            <li><a href="#">Opcja 2</a></li>
        </ul>
    </div>
</div>
```

### 7.2 Form Validation

```html
<form x-data="{
        email: '',
        password: '',
        get isValid() {
            return this.email.includes('@') && this.password.length >= 8
        }
    }"
    hx-post="{% url 'accounts:login' %}"
    hx-target="#login-result">

    <input type="email"
           x-model="email"
           :class="{ 'input-error': email && !email.includes('@') }"
           class="input input-bordered w-full">

    <input type="password"
           x-model="password"
           :class="{ 'input-error': password && password.length < 8 }"
           class="input input-bordered w-full">

    <button type="submit"
            :disabled="!isValid"
            :class="{ 'btn-disabled': !isValid }"
            class="btn btn-primary w-full">
        Zaloguj
    </button>
</form>
```

---

## 8. DATABASE BEST PRACTICES

### 8.1 QuerySet Optimization

```python
# ✅ DOBRZE - używaj select_related i prefetch_related
lessons = Lesson.objects.select_related(
    'tutor',
    'room',
    'subject',
).prefetch_related(
    'students',
    'attendance_records',
).filter(
    start_time__gte=today
)

# ❌ ŹLE - N+1 problem
for lesson in Lesson.objects.all():
    print(lesson.tutor.email)  # Każda iteracja = nowe query!
```

### 8.2 Custom Managers

```python
# apps/lessons/managers.py
from django.db import models
from django.utils import timezone


class LessonQuerySet(models.QuerySet):
    def upcoming(self):
        return self.filter(start_time__gte=timezone.now())

    def past(self):
        return self.filter(end_time__lt=timezone.now())

    def for_tutor(self, tutor):
        return self.filter(tutor=tutor)

    def for_student(self, student):
        return self.filter(students=student)

    def with_related(self):
        return self.select_related(
            'tutor', 'room', 'subject'
        ).prefetch_related('students')


class LessonManager(models.Manager):
    def get_queryset(self):
        return LessonQuerySet(self.model, using=self._db)

    def upcoming(self):
        return self.get_queryset().upcoming()

    def past(self):
        return self.get_queryset().past()
```

### 8.3 Transactions

```python
from django.db import transaction


@transaction.atomic
def create_lesson_with_students(data: dict, student_ids: list[int]) -> Lesson:
    """Tworzy lekcję z uczniami w jednej transakcji."""

    lesson = Lesson.objects.create(**data)
    lesson.students.set(student_ids)

    # Wyślij powiadomienia (Celery)
    from apps.notifications.tasks import send_lesson_notification
    transaction.on_commit(
        lambda: send_lesson_notification.delay(lesson.id)
    )

    return lesson
```

---

## 9. SECURITY

### 9.1 Middleware Order

```python
# settings/base.py
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_htmx.middleware.HtmxMiddleware',  # HTMX middleware
]
```

### 9.2 Permission Decorators

```python
from django.contrib.auth.decorators import login_required, user_passes_test


def admin_required(view_func):
    """Decorator wymagający roli admina."""
    decorated = user_passes_test(
        lambda u: u.is_authenticated and u.is_admin,
        login_url='/auth/login/'
    )(view_func)
    return login_required(decorated)


def tutor_required(view_func):
    """Decorator wymagający roli korepetytora."""
    decorated = user_passes_test(
        lambda u: u.is_authenticated and (u.is_tutor or u.is_admin),
        login_url='/auth/login/'
    )(view_func)
    return login_required(decorated)


# Użycie
@admin_required
def admin_dashboard(request):
    return render(request, 'admin/dashboard.html')
```

### 9.3 Rate Limiting

```python
from django_ratelimit.decorators import ratelimit


@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def login_view(request):
    """Logowanie z rate limiting."""
    # ... implementacja
```

---

## 10. TESTING

### 10.1 pytest Fixtures

```python
# tests/conftest.py
import pytest
from django.test import Client

from tests.factories import UserFactory, LessonFactory


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def admin_user(db):
    return UserFactory(role='admin')


@pytest.fixture
def tutor_user(db):
    return UserFactory(role='tutor')


@pytest.fixture
def student_user(db):
    return UserFactory(role='student')


@pytest.fixture
def authenticated_client(client, admin_user):
    client.force_login(admin_user)
    return client
```

### 10.2 Factory Boy

```python
# tests/factories.py
import factory
from faker import Faker

from apps.accounts.models import User
from apps.lessons.models import Lesson

fake = Faker('pl_PL')


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.LazyAttribute(lambda _: fake.user_name())
    email = factory.LazyAttribute(lambda _: fake.email())
    first_name = factory.LazyAttribute(lambda _: fake.first_name())
    last_name = factory.LazyAttribute(lambda _: fake.last_name())
    role = 'student'
    password = factory.PostGenerationMethodCall('set_password', 'testpass123')


class LessonFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Lesson

    title = factory.LazyAttribute(lambda _: fake.sentence(nb_words=3))
    tutor = factory.SubFactory(UserFactory, role='tutor')
    start_time = factory.LazyAttribute(lambda _: fake.future_datetime())
```

### 10.3 Test Examples

```python
# tests/accounts/test_views.py
import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestUserListView:
    def test_admin_can_access_user_list(self, authenticated_client):
        response = authenticated_client.get(reverse('users:list'))
        assert response.status_code == 200

    def test_htmx_returns_partial(self, authenticated_client):
        response = authenticated_client.get(
            reverse('users:list'),
            HTTP_HX_REQUEST='true',
        )
        assert response.status_code == 200
        # Partial template nie zawiera <html>
        assert b'<!DOCTYPE' not in response.content

    def test_search_filters_users(self, authenticated_client, admin_user):
        response = authenticated_client.get(
            reverse('users:list'),
            {'search': admin_user.email},
        )
        assert admin_user.email.encode() in response.content
```

---

## 11. GIT WORKFLOW

### 11.1 Branch Naming

```bash
# Features
feature/add-invoice-system
feature/student-dashboard

# Fixes
fix/login-validation
fix/calendar-timezone

# Refactoring
refactor/move-to-cbv
refactor/optimize-queries

# Docs
docs/api-documentation
docs/setup-guide
```

### 11.2 Commit Messages

```bash
# Format: <type>(<scope>): <subject>

# Types:
# feat: New feature
# fix: Bug fix
# refactor: Code refactoring
# docs: Documentation
# test: Tests
# style: Formatting
# perf: Performance
# chore: Maintenance

# Examples:
feat(auth): add direct user creation by admin
fix(calendar): correct timezone handling in lessons
refactor(views): convert user views to CBV
docs(setup): add Docker instructions
test(lessons): add integration tests for CRUD
```

### 11.3 Pre-commit Config

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.13.0
    hooks:
      - id: mypy
        additional_dependencies: [django-stubs]
```

---

## 12. FORBIDDEN PRACTICES ❌

### NIGDY nie rób tego:

```python
# ❌ Raw SQL bez potrzeby
cursor.execute("SELECT * FROM users WHERE id = %s", [user_id])

# ❌ Hardcoded credentials
DATABASE_PASSWORD = "secret123"

# ❌ Print statements w produkcji
print(f"Debug: {user}")

# ❌ Wildcard imports
from apps.accounts.models import *

# ❌ Logic w templates
{% if user.role == 'admin' and user.is_active and not user.is_deleted %}

# ❌ N+1 queries
{% for lesson in lessons %}
    {{ lesson.tutor.email }}  # Query per iteration!
{% endfor %}

# ❌ Synchronous tasks w views
send_email(user.email, subject, body)  # Use Celery!

# ❌ Brak walidacji w modelach
class User(models.Model):
    email = models.CharField(max_length=255)  # Użyj EmailField!

# ❌ Magic strings
if user.role == "admin":  # Użyj User.Role.ADMIN

# ❌ Brak type hints
def get_user(id):  # Brak typów!
    pass
```

---

## 13. PERFORMANCE METRICS

### Wymagane metryki:

- **Time to First Byte (TTFB)**: < 200ms
- **Largest Contentful Paint (LCP)**: < 2.5s
- **First Input Delay (FID)**: < 100ms
- **Database queries per request**: < 10
- **HTMX partial response**: < 100ms

### Django Debug Toolbar Checks:

- SQL queries count i czas
- Cache hits/misses
- Template rendering time
- Signal processing

---

## 14. DEVELOPMENT WORKFLOW

### Pre-commit Checklist

```bash
# 1. Format i lint
ruff check . --fix
ruff format .

# 2. Type check
mypy apps/

# 3. Tests
pytest

# 4. Migrations check
python manage.py makemigrations --check

# 5. Collectstatic (jeśli zmiany)
python manage.py collectstatic --noinput
```

### Definition of Done

- ✅ Feature działa zgodnie z wymaganiami
- ✅ Code review przeszedł
- ✅ Testy napisane i przechodzą (>80% coverage)
- ✅ Dokumentacja zaktualizowana
- ✅ Brak błędów Ruff i mypy
- ✅ Responsywny na mobile
- ✅ HTMX działa poprawnie
- ✅ Accessibility sprawdzone

---

**Ten dokument jest OBOWIĄZKOWY.**
**Każdy PR MUSI być zgodny z tymi wytycznymi.**
**Brak zgodności = odrzucenie PR.**

**Data utworzenia**: Grudzień 2025
**Wersja**: 2.0.0 (Django + HTMX)
**Następna rewizja**: Po pierwszym sprincie
