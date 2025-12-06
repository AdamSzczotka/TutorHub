# Phase 0 - Sprint 0.1: Project Initialization (Django)

## Tasks 001-008: Development Environment Setup

> **Duration**: Day 1-2 of Phase 0
> **Goal**: Complete development environment with Django, HTMX and all dependencies
> **Critical**: Foundation for all subsequent development

---

## SPRINT OVERVIEW

| Task ID | Description                     | Priority | Dependencies |
| ------- | ------------------------------- | -------- | ------------ |
| 001     | Setup Django 5.1 project        | Critical | None         |
| 002     | Configure PostgreSQL with Docker| Critical | None         |
| 003     | Setup Custom User Model         | Critical | Task 001     |
| 004     | Configure Tailwind CSS          | High     | Task 001     |
| 005     | Setup HTMX + Alpine.js          | Critical | Task 004     |
| 006     | Ruff (linting) setup            | High     | Task 001     |
| 007     | Create folder structure         | Critical | Task 001     |
| 008     | Git + pre-commit hooks          | High     | Task 006     |

---

## TASK DETAILS

### Task 001: Setup Django 5.1 Project

**Files**: `manage.py`, `napiatke/settings/`, `requirements/`

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install Django
pip install Django==5.1

# Create project
django-admin startproject napiatke .
```

**Requirements - base.txt**:

```txt
# requirements/base.txt
Django>=5.1,<5.2
psycopg2-binary>=2.9.9
django-environ>=0.11.2
django-htmx>=1.17
django-allauth>=0.61
django-imagekit>=5.0
django-crispy-forms>=2.1
crispy-tailwind>=1.0
django-filter>=24.1
Pillow>=10.2
celery[redis]>=5.3
django-celery-beat>=2.5
WeasyPrint>=61.0
whitenoise>=6.6
gunicorn>=21.2
```

```txt
# requirements/development.txt
-r base.txt
django-debug-toolbar>=4.3
django-extensions>=3.2
pytest>=8.0
pytest-django>=4.8
pytest-cov>=4.1
factory-boy>=3.3
ruff>=0.2
pre-commit>=3.6
```

**Split Settings Structure**:

```python
# napiatke/settings/__init__.py
# Empty - settings loaded via DJANGO_SETTINGS_MODULE

# napiatke/settings/base.py
import os
from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent
env = environ.Env()
environ.Env.read_env(BASE_DIR / '.env')

SECRET_KEY = env('SECRET_KEY')
DEBUG = env.bool('DEBUG', default=False)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third party
    'django_htmx',
    'allauth',
    'allauth.account',
    'crispy_forms',
    'crispy_tailwind',
    'django_filters',
    'django_celery_beat',
    # Local apps
    'apps.core',
    'apps.accounts',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_htmx.middleware.HtmxMiddleware',
]

ROOT_URLCONF = 'napiatke.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = 'tailwind'
CRISPY_TEMPLATE_PACK = 'tailwind'

# Static files
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
```

```python
# napiatke/settings/development.py
from .base import *

DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

INSTALLED_APPS += [
    'debug_toolbar',
    'django_extensions',
]

MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')

INTERNAL_IPS = ['127.0.0.1']

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME', default='napiatke'),
        'USER': env('DB_USER', default='admin'),
        'PASSWORD': env('DB_PASSWORD', default='admin123'),
        'HOST': env('DB_HOST', default='localhost'),
        'PORT': env('DB_PORT', default='5432'),
    }
}
```

```python
# napiatke/settings/production.py
from .base import *

DEBUG = False
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')

DATABASES = {
    'default': env.db('DATABASE_URL')
}

# Security
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
```

**Validation**:

```bash
python manage.py check
python manage.py runserver
# Should start on http://127.0.0.1:8000/
```

---

### Task 002: Configure PostgreSQL with Docker

**Files**: `docker-compose.yml`, `.env`, `.env.example`

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:17
    container_name: napiatke-postgres
    restart: always
    environment:
      POSTGRES_DB: napiatke
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: admin123
    ports:
      - '5432:5432'
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U admin -d napiatke"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: napiatke-redis
    restart: always
    ports:
      - '6379:6379'
    volumes:
      - redis_data:/data

  adminer:
    image: adminer:latest
    container_name: napiatke-adminer
    restart: always
    ports:
      - '8080:8080'
    depends_on:
      - postgres

volumes:
  postgres_data:
  redis_data:
```

**Environment Variables**:

```env
# .env.example (copy to .env)
SECRET_KEY=your-super-secret-key-change-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=napiatke
DB_USER=admin
DB_PASSWORD=admin123
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

**Validation**:

```bash
docker-compose up -d
# Wait for services to start
docker-compose ps  # All services should be "Up"
# Access Adminer at http://localhost:8080
# Server: postgres, User: admin, Password: admin123, Database: napiatke
```

---

### Task 003: Setup Custom User Model

**Files**: `apps/accounts/models.py`, `apps/accounts/managers.py`

**CRITICAL**: Must be done BEFORE first migration!

```bash
# Create accounts app
mkdir -p apps/accounts
python manage.py startapp accounts apps/accounts
```

```python
# apps/accounts/managers.py
from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')
        return self.create_user(email, password, **extra_fields)
```

```python
# apps/accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

from .managers import UserManager


class UserRole(models.TextChoices):
    ADMIN = 'admin', 'Administrator'
    TUTOR = 'tutor', 'Korepetytor'
    STUDENT = 'student', 'Uczeń'


class User(AbstractUser):
    """Custom User model with email as username."""

    username = None  # Remove username field
    email = models.EmailField('Email', unique=True)

    # Profile fields
    role = models.CharField(
        'Rola',
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.STUDENT,
    )
    phone = models.CharField('Telefon', max_length=20, blank=True)
    avatar = models.ImageField(
        'Avatar',
        upload_to='avatars/',
        blank=True,
        null=True,
    )

    # Status flags
    is_profile_completed = models.BooleanField(
        'Profil uzupełniony',
        default=False,
    )
    first_login = models.BooleanField(
        'Pierwsze logowanie',
        default=True,
    )

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        db_table = 'users'
        verbose_name = 'Użytkownik'
        verbose_name_plural = 'Użytkownicy'

    def __str__(self):
        return f'{self.get_full_name()} ({self.email})'

    @property
    def is_admin(self):
        return self.role == UserRole.ADMIN

    @property
    def is_tutor(self):
        return self.role == UserRole.TUTOR

    @property
    def is_student(self):
        return self.role == UserRole.STUDENT
```

```python
# apps/accounts/apps.py
from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.accounts'
    verbose_name = 'Konta użytkowników'
```

```python
# apps/accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'first_name', 'last_name', 'role', 'is_active']
    list_filter = ['role', 'is_active', 'is_staff']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['email']

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Dane osobowe', {'fields': ('first_name', 'last_name', 'phone', 'avatar')}),
        ('Rola', {'fields': ('role', 'is_profile_completed', 'first_login')}),
        ('Uprawnienia', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Daty', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'role', 'password1', 'password2'),
        }),
    )
```

**Run Initial Migration**:

```bash
python manage.py makemigrations accounts
python manage.py migrate
python manage.py createsuperuser
```

---

### Task 004: Configure Tailwind CSS

**Files**: `static/css/input.css`, `static/css/output.css`, `package.json`

**Option A: Standalone Tailwind CLI (Recommended)**

```bash
# Download Tailwind CLI
# Windows:
curl -sLO https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-windows-x64.exe
mv tailwindcss-windows-x64.exe tailwindcss.exe

# Linux/Mac:
curl -sLO https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-linux-x64
chmod +x tailwindcss-linux-x64
mv tailwindcss-linux-x64 tailwindcss
```

```javascript
// tailwind.config.js
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './apps/**/templates/**/*.html',
    './static/js/**/*.js',
  ],
  theme: {
    extend: {},
  },
  plugins: [
    require('daisyui'),
  ],
  daisyui: {
    themes: ['light', 'dark', 'corporate'],
    darkTheme: 'dark',
    base: true,
    styled: true,
    utils: true,
  },
}
```

```css
/* static/css/input.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

/* Custom styles */
@layer components {
  .btn-primary {
    @apply btn btn-primary;
  }

  .card-shadow {
    @apply shadow-lg hover:shadow-xl transition-shadow;
  }
}
```

**Option B: npm with daisyUI**

```bash
npm init -y
npm install -D tailwindcss daisyui
npx tailwindcss init
```

**Build Command (add to package.json or Makefile)**:

```bash
# Development (watch mode)
./tailwindcss -i ./static/css/input.css -o ./static/css/output.css --watch

# Production
./tailwindcss -i ./static/css/input.css -o ./static/css/output.css --minify
```

**Validation**:

```bash
# Build CSS
./tailwindcss -i ./static/css/input.css -o ./static/css/output.css
# Check output.css is created and contains styles
```

---

### Task 005: Setup HTMX + Alpine.js

**Files**: `templates/base.html`, `static/js/`

**Download Libraries**:

```bash
# Create static/js directory
mkdir -p static/js

# Download HTMX
curl -o static/js/htmx.min.js https://unpkg.com/htmx.org@2.0.0/dist/htmx.min.js

# Download Alpine.js
curl -o static/js/alpine.min.js https://unpkg.com/alpinejs@3.14.0/dist/cdn.min.js
```

**Base Template**:

```html
<!-- templates/base.html -->
{% load static %}
<!DOCTYPE html>
<html lang="pl" data-theme="corporate">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Na Piątkę{% endblock %}</title>

    <!-- Tailwind CSS -->
    <link rel="stylesheet" href="{% static 'css/output.css' %}">

    <!-- HTMX -->
    <script src="{% static 'js/htmx.min.js' %}" defer></script>

    <!-- Alpine.js -->
    <script src="{% static 'js/alpine.min.js' %}" defer></script>

    {% block extra_css %}{% endblock %}
</head>
<body class="min-h-screen bg-base-200"
      hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'>

    {% block navbar %}{% endblock %}

    <main class="container mx-auto px-4 py-8">
        {% block content %}{% endblock %}
    </main>

    <!-- Toast notifications -->
    <div id="toast-container"
         class="toast toast-end"
         hx-swap-oob="true">
        {% if messages %}
            {% for message in messages %}
                <div class="alert alert-{{ message.tags }}"
                     x-data="{ show: true }"
                     x-show="show"
                     x-init="setTimeout(() => show = false, 5000)">
                    <span>{{ message }}</span>
                </div>
            {% endfor %}
        {% endif %}
    </div>

    <!-- Modal container -->
    <div id="modal-container"></div>

    {% block extra_js %}{% endblock %}
</body>
</html>
```

**HTMX Configuration**:

```javascript
// static/js/htmx-config.js
document.addEventListener('DOMContentLoaded', function() {
    // Configure HTMX
    htmx.config.defaultSwapStyle = 'innerHTML';
    htmx.config.historyCacheSize = 10;

    // Global error handling
    document.body.addEventListener('htmx:responseError', function(event) {
        console.error('HTMX Error:', event.detail);
        // Show error toast
        const toast = document.getElementById('toast-container');
        toast.innerHTML = `
            <div class="alert alert-error">
                <span>Wystąpił błąd. Spróbuj ponownie.</span>
            </div>
        `;
    });

    // Loading indicator
    htmx.on('htmx:beforeRequest', function(event) {
        event.target.classList.add('loading');
    });

    htmx.on('htmx:afterRequest', function(event) {
        event.target.classList.remove('loading');
    });
});
```

**Validation**:

```bash
python manage.py runserver
# Open browser, check that HTMX and Alpine are loaded (no console errors)
```

---

### Task 006: Ruff (Linting) Setup

**Files**: `pyproject.toml`, `.pre-commit-config.yaml`

```toml
# pyproject.toml
[project]
name = "napiatke"
version = "1.0.0"
requires-python = ">=3.11"

[tool.ruff]
target-version = "py311"
line-length = 88
exclude = [
    ".git",
    "__pycache__",
    "migrations",
    ".venv",
    "venv",
    "staticfiles",
]

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
    "DJ",  # flake8-django
]
ignore = [
    "E501",  # line too long (handled by formatter)
]

[tool.ruff.lint.isort]
known-first-party = ["apps", "napiatke"]
section-order = ["future", "standard-library", "django", "third-party", "first-party", "local-folder"]

[tool.ruff.lint.isort.sections]
django = ["django"]

[tool.ruff.format]
quote-style = "single"
indent-style = "space"
docstring-code-format = true

[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "napiatke.settings.development"
python_files = ["test_*.py", "*_test.py"]
addopts = "-v --tb=short"
```

**Validation**:

```bash
# Install ruff
pip install ruff

# Check code
ruff check .

# Format code
ruff format .

# Fix issues automatically
ruff check --fix .
```

---

### Task 007: Create Folder Structure

**Goal**: Implement exact structure from ImplementationGuidelines.md

```bash
# Create main directories
mkdir -p apps/{core,accounts,tutors,students,lessons,rooms,subjects,attendance,cancellations,invoices,messages,notifications,reports,landing}
mkdir -p templates/{components,partials,admin_panel,tutor_panel,student_panel}
mkdir -p static/{css,js,img}
mkdir -p media
mkdir -p requirements
mkdir -p tests/{unit,integration,e2e}

# Create __init__.py files for Python packages
touch apps/__init__.py
for dir in apps/*/; do touch "$dir/__init__.py"; done

# Create placeholder files
touch templates/components/_button.html
touch templates/components/_modal.html
touch templates/components/_table.html
touch templates/components/_card.html
touch templates/components/_form_field.html
touch templates/partials/_empty.html
```

**Core App Setup**:

```python
# apps/core/mixins.py
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpResponse


class HTMXMixin:
    """Mixin for HTMX-aware views."""

    def get_template_names(self):
        if getattr(self.request, 'htmx', False):
            return [self.partial_template_name]
        return super().get_template_names()


class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin requiring admin role."""

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_admin


class TutorRequiredMixin(UserPassesTestMixin):
    """Mixin requiring tutor role."""

    def test_func(self):
        user = self.request.user
        return user.is_authenticated and (user.is_tutor or user.is_admin)
```

```python
# apps/core/utils.py
from django.http import HttpResponse


def htmx_redirect(url: str) -> HttpResponse:
    """Return HTMX redirect response."""
    response = HttpResponse()
    response['HX-Redirect'] = url
    return response


def htmx_refresh() -> HttpResponse:
    """Return HTMX refresh response."""
    response = HttpResponse()
    response['HX-Refresh'] = 'true'
    return response
```

---

### Task 008: Git + Pre-commit Hooks

**Files**: `.pre-commit-config.yaml`, `.gitignore`

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.2.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: local
    hooks:
      - id: django-check
        name: Django Check
        entry: python manage.py check
        language: system
        pass_filenames: false
        always_run: true
```

```gitignore
# .gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
.venv/
ENV/

# Django
*.log
local_settings.py
db.sqlite3
media/
staticfiles/

# IDE
.idea/
.vscode/
*.swp
*.swo

# Environment
.env
.env.local
.env.*.local

# Testing
.coverage
htmlcov/
.pytest_cache/
.tox/

# Build
*.egg-info/
dist/
build/

# Tailwind
node_modules/
static/css/output.css

# OS
.DS_Store
Thumbs.db
```

**Setup Pre-commit**:

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

**Validation**:

```bash
git add .
git commit -m "feat: initial Django project setup"
# Pre-commit hooks should run and pass
```

---

## COMPLETION CHECKLIST

### Technical Validation

- [ ] Django app starts on `python manage.py runserver`
- [ ] Database connection working (PostgreSQL)
- [ ] Redis connection working
- [ ] Custom User model created before migrations
- [ ] Admin panel accessible at `/admin/`
- [ ] Tailwind CSS compiled and working
- [ ] HTMX loaded (check browser console)
- [ ] Alpine.js loaded (check browser console)
- [ ] Ruff passes with zero errors
- [ ] Pre-commit hooks working
- [ ] All folder structure matches guidelines

### Environment Files

- [ ] `.env.example` created with all variables
- [ ] `.env` created (gitignored)
- [ ] `requirements/base.txt` complete
- [ ] `requirements/development.txt` complete
- [ ] `docker-compose.yml` working

### Documentation

- [ ] README.md updated with setup instructions
- [ ] Environment variables documented
- [ ] Docker setup instructions clear
- [ ] Development workflow documented

### Next Steps

- [ ] Ready for Phase 1: Foundation development
- [ ] Team members can clone and setup locally
- [ ] CI/CD pipeline can be configured
- [ ] Production deployment preparation possible

---

## QUICK START COMMANDS

```bash
# 1. Clone and setup
git clone <repo>
cd napiatke
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 2. Install dependencies
pip install -r requirements/development.txt

# 3. Start services
docker-compose up -d

# 4. Setup environment
cp .env.example .env
# Edit .env with your settings

# 5. Run migrations
python manage.py migrate
python manage.py createsuperuser

# 6. Build Tailwind (in separate terminal)
./tailwindcss -i ./static/css/input.css -o ./static/css/output.css --watch

# 7. Run development server
python manage.py runserver
```

---

## TROUBLESHOOTING

### Common Issues

**Database Connection Failed**:

```bash
docker-compose down
docker-compose up -d
# Wait 10 seconds for PostgreSQL to be ready
python manage.py migrate
```

**Custom User Model Errors**:

```bash
# If you already ran migrations before creating User model:
# 1. Delete all migrations in apps/*/migrations/
# 2. Drop database: docker-compose down -v
# 3. Start fresh: docker-compose up -d
# 4. Run: python manage.py makemigrations && python manage.py migrate
```

**Tailwind Not Compiling**:

```bash
# Check tailwind.config.js content paths
# Run manually:
./tailwindcss -i ./static/css/input.css -o ./static/css/output.css
```

**Pre-commit Hook Failures**:

```bash
# Skip hooks temporarily (not recommended)
git commit --no-verify -m "message"

# Fix issues
ruff check --fix .
ruff format .
pre-commit run --all-files
```

---

## SUCCESS METRICS

| Metric | Target |
|--------|--------|
| Setup time | <4 hours |
| Ruff errors | 0 |
| Django check | No issues |
| Docker services | All running |
| Database | Connected |
| Static files | Compiled |

---

**Phase Completion**: When all 8 tasks validated
**Next Phase**: Phase 1 - Foundation (Database Models & Authentication)
