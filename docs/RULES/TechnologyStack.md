# Technology Stack Documentation

## System Zarządzania Szkołą Korepetycyjną "Na Piątkę"

> **WAŻNE**: Ten dokument stanowi sztywny kontrakt technologiczny dla projektu.
> Wszystkie wymienione technologie i wersje są finalne i nie podlegają zmianom podczas 3-miesięcznego okresu developmentu.
> Data utworzenia: Grudzień 2025
> **Aktualizacja**: Zmiana stacku z Next.js na Django + HTMX

---

## 1. CORE STACK

### Runtime & Framework

- **Python**: 3.12.x (najnowsza stabilna)
- **Django**: 5.1.x (najnowsza stabilna)
- **HTMX**: 2.0.x (interaktywność bez JS)
- **Alpine.js**: 3.14.x (lekka reaktywność)

### Architektura

```
Frontend (Django Templates + HTMX) → Django Views → Django ORM → PostgreSQL
```

**Wzorzec architektoniczny**: Monolityczna aplikacja Django z server-side rendering i HTMX dla dynamicznych aktualizacji.

---

## 2. BACKEND & API

### Web Framework

- **Django**: 5.1.x
  - django-environ: 0.11.x (zmienne środowiskowe)
  - django-extensions: 3.2.x (development helpers)
  - django-debug-toolbar: 4.4.x (debugging)

### HTMX Integration

- **django-htmx**: 1.19.x
  - Middleware i context processors
  - Helper functions dla partial responses
  - Request detection (request.htmx)

### Database Access

- **Django ORM**: Wbudowany (zamiennik Prisma)
  - Migracje: django-admin migrate
  - QuerySets dla złożonych zapytań
  - Select_related / Prefetch_related dla optymalizacji

### Forms & Validation

- **Django Forms**: Wbudowany system formularzy
- **django-crispy-forms**: 2.3.x (renderowanie formularzy)
- **crispy-tailwind**: 1.0.x (Tailwind support)

---

## 3. FRONTEND

### Templating Engine

- **Django Templates**: Wbudowany system szablonów
  - Template tags i filters
  - Template inheritance (extends/block)
  - Includes dla komponentów

### Interaktywność (HTMX)

- **HTMX**: 2.0.x
  - hx-get, hx-post: AJAX requests
  - hx-trigger: Event handling
  - hx-target: DOM updates
  - hx-swap: Content replacement
  - hx-push-url: History management

### Reaktywność (Alpine.js)

- **Alpine.js**: 3.14.x
  - x-data: Deklaracja stanu
  - x-show/x-if: Warunkowe wyświetlanie
  - x-for: Pętle
  - x-on: Event handling
  - x-model: Two-way binding

### CSS Framework

- **Tailwind CSS**: 3.4.x
  - PostCSS: 8.4.x
  - Autoprefixer: 10.4.x
  - django-tailwind: 3.8.x LUB standalone Tailwind CLI

### Komponenty UI

- **daisyUI**: 4.12.x (komponenty Tailwind)
  - Alternatywa dla shadcn/ui
  - Gotowe komponenty: buttons, modals, cards
  - Theming support

### Ikony

- **Heroicons**: 2.x (SVG ikony)
- **Lucide Icons**: Alternatywa

---

## 4. DATABASE

### Główna Baza Danych

- **PostgreSQL**: 17.x
  - Połączenie przez psycopg2-binary
  - Connection pooling (opcjonalnie django-db-connection-pool)
  - SSL w produkcji

### Cache & Session

- **Redis**: 7.x
  - django-redis: 5.4.x
  - Cache backend
  - Session backend
  - Celery broker

---

## 5. AUTHENTICATION & SECURITY

### Autoryzacja

- **Django Auth**: Wbudowany system
  - Custom User model (AbstractUser)
  - Permission system
  - Groups

- **django-allauth**: 65.x (opcjonalnie)
  - Social auth (jeśli potrzebne)
  - Email verification
  - Password reset

### Bezpieczeństwo

- **Django Security Middleware**: Wbudowane
  - CSRF protection
  - XSS prevention
  - SQL injection protection (ORM)
  - Clickjacking protection

- **bcrypt**: Przez Django (PASSWORD_HASHERS)
- **django-cors-headers**: 4.4.x (CORS dla API)

### Rate Limiting

- **django-ratelimit**: 4.1.x
- **django-axes**: 7.x (brute force protection)

---

## 6. BACKGROUND TASKS & QUEUE

### Task Queue

- **Celery**: 5.4.x
  - celery[redis]: Redis jako broker
  - django-celery-beat: 2.6.x (periodic tasks)
  - django-celery-results: 2.5.x (result backend)

### Scheduler

- **Celery Beat**: Wbudowany w Celery
  - Cron-like scheduling
  - Database scheduler

---

## 7. EMAIL & NOTIFICATIONS

### Email

- **Django Email**: Wbudowany
  - SMTP backend
  - Console backend (development)

- **django-anymail**: 12.x (produkcja)
  - Resend support
  - SendGrid support
  - Mailgun support

### Templating Emaili

- **Django Templates**: Dla email templates
- Alternatywa: mjml dla responsywnych emaili

---

## 8. KALENDARZ & DATY

### Komponenty Kalendarza

- **FullCalendar**: 6.1.x (JavaScript)
  - @fullcalendar/core
  - @fullcalendar/daygrid
  - @fullcalendar/timegrid
  - @fullcalendar/interaction
  - Integracja przez HTMX events

### Obsługa Dat (Python)

- **datetime**: Wbudowany
- **python-dateutil**: 2.9.x
- **django-timezone-field**: 7.x (timezone support)

---

## 9. FILE HANDLING & MEDIA

### Upload Plików

- **Django FileField/ImageField**: Wbudowane
- **Pillow**: 11.x (image processing)
- **django-imagekit**: 5.x (thumbnails, processing)

### Storage

- **Local Storage**: Development
- **django-storages**: 1.14.x (production)
  - S3 compatible storage
  - Azure Blob Storage

---

## 10. PDF GENERATION

### Generowanie Faktur/Raportów

- **WeasyPrint**: 62.x (HTML to PDF)
  - Rekomendowany dla Django
  - Obsługa CSS
  - Polskie znaki

- **Alternatywa**: xhtml2pdf 0.2.x

---

## 11. DEVELOPMENT TOOLS

### Testing

- **pytest**: 8.x
- **pytest-django**: 4.9.x
- **pytest-cov**: 5.x (coverage)
- **factory-boy**: 3.3.x (fixtures)
- **faker**: 30.x (fake data)

### E2E Testing

- **Playwright**: 1.49.x
- **Selenium**: 4.x (alternatywa)

### Linting & Formatting

- **Ruff**: 0.8.x (linter + formatter - zamiennik flake8/black/isort)
- **pre-commit**: 4.x (git hooks)
- **mypy**: 1.13.x (type checking)

### Development Server

- **Django runserver**: Development
- **django-browser-reload**: 1.x (auto-reload z HTMX)

---

## 12. DEVOPS & DEPLOYMENT

### Konteneryzacja

- **Docker**: 27.x
- **Docker Compose**: 2.x

### WSGI/ASGI Server

- **Gunicorn**: 23.x (WSGI)
- **Uvicorn**: 0.32.x (ASGI, jeśli async potrzebne)

### Reverse Proxy

- **Nginx**: 1.27.x
- **Caddy**: 2.x (alternatywa, auto SSL)

### Static Files

- **WhiteNoise**: 6.8.x (serving static files)
- **django-compressor**: 4.5.x (opcjonalnie)

### CI/CD

- **GitHub Actions**: Najnowsza wersja

### Hosting

- **Railway**: Rekomendowany (prosty deployment)
- **Render**: Alternatywa
- **DigitalOcean App Platform**: Alternatywa
- **Neon**: PostgreSQL hosting

### Monitoring

- **Sentry**: sentry-sdk 2.x
- **django-silk**: 5.x (profiling, opcjonalnie)

---

## 13. STRUKTURA PROJEKTU

```
napiatke/
├── manage.py                    # Django CLI
├── napiatke/                    # Główny projekt
│   ├── __init__.py
│   ├── settings/               # Podzielone ustawienia
│   │   ├── __init__.py
│   │   ├── base.py             # Wspólne ustawienia
│   │   ├── development.py      # Dev settings
│   │   └── production.py       # Prod settings
│   ├── urls.py                  # Główne URL routing
│   ├── wsgi.py                  # WSGI entry point
│   ├── asgi.py                  # ASGI entry point
│   └── celery.py                # Celery config
│
├── apps/                        # Django apps
│   ├── core/                    # Wspólne utilities
│   │   ├── models.py           # Base models
│   │   ├── mixins.py           # View mixins
│   │   └── utils.py            # Helper functions
│   ├── accounts/                # Auth & Users
│   │   ├── models.py           # User model
│   │   ├── views.py            # Auth views
│   │   ├── forms.py            # Login/register forms
│   │   └── urls.py
│   ├── tutors/                  # Tutor profiles
│   ├── students/                # Student profiles
│   ├── lessons/                 # Lessons & Calendar
│   ├── rooms/                   # Room management
│   ├── subjects/                # Subjects & Levels
│   ├── attendance/              # Attendance system
│   ├── cancellations/           # Cancellation & makeup
│   ├── invoices/                # Billing system
│   ├── messages/                # Internal messaging
│   ├── notifications/           # Notification system
│   ├── reports/                 # Reports & statistics
│   └── landing/                 # Public landing page
│
├── templates/                   # Django templates
│   ├── base.html               # Base template
│   ├── components/              # Reusable components
│   │   ├── _button.html
│   │   ├── _modal.html
│   │   ├── _table.html
│   │   ├── _card.html
│   │   ├── _form_field.html
│   │   └── _pagination.html
│   ├── layouts/                 # Layout templates
│   │   ├── admin.html
│   │   ├── tutor.html
│   │   └── student.html
│   ├── partials/                # HTMX partial responses
│   │   ├── users/
│   │   ├── lessons/
│   │   └── ...
│   └── emails/                  # Email templates
│
├── static/                      # Static files
│   ├── css/
│   │   ├── input.css           # Tailwind input
│   │   └── output.css          # Tailwind output
│   ├── js/
│   │   ├── htmx.min.js
│   │   ├── alpine.min.js
│   │   └── app.js              # Custom JS
│   └── img/
│
├── media/                       # User uploads
│
├── locale/                      # Translations (i18n)
│   └── pl/
│
├── docker/
│   ├── Dockerfile
│   ├── Dockerfile.prod
│   └── nginx.conf
│
├── docker-compose.yml
├── docker-compose.prod.yml
│
├── requirements/
│   ├── base.txt
│   ├── development.txt
│   └── production.txt
│
├── pyproject.toml               # Ruff, mypy config
├── pytest.ini
├── .pre-commit-config.yaml
├── .env.example
└── README.md
```

---

## 14. REQUIREMENTS FILES

### requirements/base.txt

```txt
# Django
Django>=5.1,<5.2
django-environ>=0.11
django-extensions>=3.2

# HTMX
django-htmx>=1.19

# Database
psycopg2-binary>=2.9

# Forms
django-crispy-forms>=2.3
crispy-tailwind>=1.0

# Auth
django-allauth>=65.0

# Cache & Sessions
django-redis>=5.4

# Background Tasks
celery[redis]>=5.4
django-celery-beat>=2.6
django-celery-results>=2.5

# Files & Images
Pillow>=11.0
django-imagekit>=5.0

# PDF
WeasyPrint>=62.0

# Security
django-cors-headers>=4.4
django-ratelimit>=4.1

# Utils
python-dateutil>=2.9
```

### requirements/development.txt

```txt
-r base.txt

# Debug
django-debug-toolbar>=4.4
django-browser-reload>=1.0

# Testing
pytest>=8.0
pytest-django>=4.9
pytest-cov>=5.0
factory-boy>=3.3
faker>=30.0

# Linting
ruff>=0.8
mypy>=1.13
django-stubs>=5.1
pre-commit>=4.0
```

### requirements/production.txt

```txt
-r base.txt

# Server
gunicorn>=23.0
whitenoise>=6.8

# Storage
django-storages>=1.14
boto3>=1.35

# Monitoring
sentry-sdk>=2.0

# Email
django-anymail>=12.0
```

---

## 15. ZMIENNE ŚRODOWISKOWE

```env
# Django
DJANGO_SECRET_KEY="your-secret-key-min-50-chars"
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL="postgresql://user:password@localhost:5432/napiatke"

# Redis
REDIS_URL="redis://localhost:6379/0"

# Email
EMAIL_HOST=smtp.resend.com
EMAIL_PORT=587
EMAIL_HOST_USER=resend
EMAIL_HOST_PASSWORD=re_...
DEFAULT_FROM_EMAIL=noreply@napiatke.pl

# Celery
CELERY_BROKER_URL="redis://localhost:6379/1"

# Sentry (Production)
SENTRY_DSN=""

# Storage (Production)
AWS_ACCESS_KEY_ID=""
AWS_SECRET_ACCESS_KEY=""
AWS_STORAGE_BUCKET_NAME=""
```

---

## 16. KOMENDY STARTOWE

```bash
# Utworzenie virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Instalacja zależności
pip install -r requirements/development.txt

# Docker (PostgreSQL + Redis)
docker-compose up -d

# Migracje
python manage.py migrate

# Superuser
python manage.py createsuperuser

# Tailwind (kompilacja CSS)
npx tailwindcss -i static/css/input.css -o static/css/output.css --watch

# Development server
python manage.py runserver

# Celery worker
celery -A napiatke worker -l info

# Celery beat
celery -A napiatke beat -l info
```

---

## 17. ZASADY DEVELOPMENTU

1. **Django Apps** - każda funkcjonalność jako osobna app
2. **Class-Based Views** - preferowane nad function-based
3. **HTMX dla interaktywności** - zamiast JavaScript frameworks
4. **Alpine.js dla stanu lokalnego** - tylko gdy HTMX nie wystarczy
5. **Django Forms** - do walidacji i renderowania
6. **Django ORM** - brak raw SQL (chyba że konieczne)
7. **Celery** - dla wszystkich background tasks
8. **pytest** - dla wszystkich testów
9. **Ruff** - dla lintingu i formatowania
10. **Git flow** z feature branches

---

## 18. PORÓWNANIE ZE STARYM STACKIEM

| Komponent | Stary (Next.js) | Nowy (Django) |
|-----------|-----------------|---------------|
| Framework | Next.js 15.5 | Django 5.1 |
| Language | TypeScript | Python |
| API | tRPC | Django Views |
| ORM | Prisma | Django ORM |
| Auth | NextAuth.js | Django Auth/Allauth |
| Forms | React Hook Form + Zod | Django Forms |
| State | Zustand + React Query | HTMX + Alpine.js |
| UI Components | shadcn/ui | daisyUI |
| CSS | Tailwind CSS 4 | Tailwind CSS 3.4 |
| Real-time | Pusher | HTMX polling/WebSocket |
| Queue | BullMQ | Celery |
| Testing | Vitest + Playwright | pytest + Playwright |

---

**Ten dokument jest ostateczny i obowiązujący.**
**Data zatwierdzenia: Grudzień 2025**
**Okres obowiązywania: 3 miesiące**
