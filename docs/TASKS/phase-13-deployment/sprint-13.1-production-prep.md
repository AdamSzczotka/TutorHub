# Phase 13 - Sprint 13.1: Production Preparation (Django)

## Tasks 153-157: Production Environment Setup & Monitoring

> **Duration**: Week 17 (First half of Phase 13 - FINAL PHASE)
> **Goal**: Prepare production infrastructure, monitoring, backups, and analytics
> **Dependencies**: All phases 0-12 completed (Full system built and tested)

---

## SPRINT OVERVIEW

| Task ID | Description                           | Priority | Dependencies       |
| ------- | ------------------------------------- | -------- | ------------------ |
| 153     | Production environment setup (Docker) | Critical | All features ready |
| 154     | Production database migration         | Critical | Task 153           |
| 155     | Error tracking & monitoring (Sentry)  | Critical | Task 153           |
| 156     | Analytics & logging setup             | High     | Task 153           |
| 157     | Automated backup configuration        | Critical | Task 154           |

---

## PRODUCTION ENVIRONMENT SETUP

### Docker Production Configuration

**File**: `docker-compose.prod.yml`

```yaml
version: '3.8'

services:
  web:
    build:
      context: .
      dockerfile: Dockerfile.prod
    container_name: napiatke_web
    restart: always
    environment:
      - DJANGO_SETTINGS_MODULE=napiatke.settings.production
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - SECRET_KEY=${SECRET_KEY}
      - ALLOWED_HOSTS=${ALLOWED_HOSTS}
      - SENTRY_DSN=${SENTRY_DSN}
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
    volumes:
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health/"]
      interval: 30s
      timeout: 10s
      retries: 3

  db:
    image: postgres:17-alpine
    container_name: napiatke_db
    restart: always
    environment:
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: napiatke_redis
    restart: always
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  celery:
    build:
      context: .
      dockerfile: Dockerfile.prod
    container_name: napiatke_celery
    restart: always
    command: celery -A napiatke worker -l info
    environment:
      - DJANGO_SETTINGS_MODULE=napiatke.settings.production
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    depends_on:
      - db
      - redis

  celery-beat:
    build:
      context: .
      dockerfile: Dockerfile.prod
    container_name: napiatke_celery_beat
    restart: always
    command: celery -A napiatke beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
    environment:
      - DJANGO_SETTINGS_MODULE=napiatke.settings.production
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    depends_on:
      - db
      - redis
      - celery

  nginx:
    image: nginx:alpine
    container_name: napiatke_nginx
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - static_volume:/var/www/static:ro
      - media_volume:/var/www/media:ro
    depends_on:
      - web

volumes:
  postgres_data:
  redis_data:
  static_volume:
  media_volume:
```

### Production Dockerfile

**File**: `Dockerfile.prod`

```dockerfile
# Multi-stage build for production
FROM python:3.12-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements/production.txt .
RUN pip install --no-cache-dir -r production.txt

# Production image
FROM python:3.12-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user
RUN groupadd -r django && useradd -r -g django django

# Copy application
COPY --chown=django:django . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Switch to non-root user
USER django

# Expose port
EXPOSE 8000

# Run Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--threads", "2", "napiatke.wsgi:application"]
```

### Nginx Configuration

**File**: `nginx/nginx.conf`

```nginx
upstream django {
    server web:8000;
}

server {
    listen 80;
    server_name napiatke.pl www.napiatke.pl;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name napiatke.pl www.napiatke.pl;

    # SSL Configuration
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;

    # Security Headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' cdn.jsdelivr.net unpkg.com; style-src 'self' 'unsafe-inline' fonts.googleapis.com; font-src 'self' fonts.gstatic.com; img-src 'self' data: https:; connect-src 'self';" always;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml text/javascript;

    # Static files
    location /static/ {
        alias /var/www/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias /var/www/media/;
        expires 1M;
        add_header Cache-Control "public";
    }

    # Favicon
    location /favicon.ico {
        alias /var/www/static/img/favicon.ico;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Django application
    location / {
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check (no logging)
    location /api/health/ {
        access_log off;
        proxy_pass http://django;
        proxy_set_header Host $host;
    }

    # Error pages
    error_page 500 502 503 504 /50x.html;
    location = /50x.html {
        root /usr/share/nginx/html;
    }
}
```

### Production Settings

**File**: `napiatke/settings/production.py`

```python
from .base import *
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.redis import RedisIntegration

DEBUG = False

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['napiatke.pl', 'www.napiatke.pl'])

# Security Settings
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Strict'
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_TRUSTED_ORIGINS = ['https://napiatke.pl', 'https://www.napiatke.pl']

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS = 63072000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('POSTGRES_DB'),
        'USER': env('POSTGRES_USER'),
        'PASSWORD': env('POSTGRES_PASSWORD'),
        'HOST': env('POSTGRES_HOST', default='db'),
        'PORT': env('POSTGRES_PORT', default='5432'),
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'connect_timeout': 10,
        },
    }
}

# Cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': env('REDIS_URL', default='redis://redis:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'napiatke',
        'TIMEOUT': 300,
    }
}

# Session
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Email
EMAIL_BACKEND = 'anymail.backends.resend.EmailBackend'
ANYMAIL = {
    'RESEND_API_KEY': env('RESEND_API_KEY'),
}
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='Na Piątkę <noreply@napiatke.pl>')

# Celery
CELERY_BROKER_URL = env('REDIS_URL', default='redis://redis:6379/0')
CELERY_RESULT_BACKEND = env('REDIS_URL', default='redis://redis:6379/0')

# Sentry
sentry_sdk.init(
    dsn=env('SENTRY_DSN'),
    integrations=[
        DjangoIntegration(),
        CeleryIntegration(),
        RedisIntegration(),
    ],
    traces_sample_rate=0.1,
    profiles_sample_rate=0.1,
    send_default_pii=False,
    environment='production',
)

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/napiatke/django.log',
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['console', 'file'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}
```

### Environment Variables Template

**File**: `.env.production.example`

```env
# Django
DJANGO_SETTINGS_MODULE=napiatke.settings.production
SECRET_KEY=your-super-secret-key-change-me
ALLOWED_HOSTS=napiatke.pl,www.napiatke.pl

# Database
POSTGRES_DB=napiatke
POSTGRES_USER=napiatke
POSTGRES_PASSWORD=your-secure-password
POSTGRES_HOST=db
POSTGRES_PORT=5432
DATABASE_URL=postgresql://napiatke:password@db:5432/napiatke

# Redis
REDIS_URL=redis://redis:6379/0

# Email (Resend)
RESEND_API_KEY=re_xxxxxxxxxxxxxxxxx
DEFAULT_FROM_EMAIL=Na Piątkę <noreply@napiatke.pl>

# Sentry
SENTRY_DSN=https://xxx@xxx.ingest.sentry.io/xxx

# Admin
ADMIN_EMAIL=admin@napiatke.pl
```

---

## PRODUCTION DATABASE MIGRATION

### Migration Script

**File**: `scripts/migrate-production.sh`

```bash
#!/bin/bash
set -e

echo "==================================="
echo "Production Database Migration"
echo "==================================="

# Check environment
if [ -z "$DATABASE_URL" ]; then
    echo "Error: DATABASE_URL not set"
    exit 1
fi

# Confirmation
read -p "This will migrate PRODUCTION database. Continue? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Migration cancelled"
    exit 0
fi

# Create backup first
echo "Creating backup..."
BACKUP_FILE="backups/pre-migration-$(date +%Y%m%d-%H%M%S).sql"
mkdir -p backups
docker exec napiatke_db pg_dump -U $POSTGRES_USER $POSTGRES_DB > $BACKUP_FILE
echo "Backup saved: $BACKUP_FILE"

# Run migrations
echo "Running migrations..."
docker exec napiatke_web python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
docker exec napiatke_web python manage.py collectstatic --noinput

echo "Migration complete!"
```

### Production Seed Script

**File**: `apps/core/management/commands/seed_production.py`

```python
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.subjects.models import Subject, Level
from apps.rooms.models import Room

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed production database with initial data'

    def handle(self, *args, **options):
        self.stdout.write('Seeding production database...')

        # 1. Create admin user
        admin_password = 'Admin2025!@#CHANGE_ME'
        admin, created = User.objects.update_or_create(
            email='admin@napiatke.pl',
            defaults={
                'first_name': 'System',
                'last_name': 'Administrator',
                'role': 'ADMIN',
                'is_active': True,
                'first_login': True,
            }
        )
        if created:
            admin.set_password(admin_password)
            admin.save()
            self.stdout.write(self.style.SUCCESS(f'Admin created: {admin.email}'))
            self.stdout.write(self.style.WARNING(f'DEFAULT PASSWORD: {admin_password}'))
            self.stdout.write(self.style.WARNING('CHANGE THIS IMMEDIATELY!'))

        # 2. Create subjects
        subjects = [
            {'name': 'Matematyka', 'color': '#EF4444'},
            {'name': 'Język Polski', 'color': '#3B82F6'},
            {'name': 'Język Angielski', 'color': '#10B981'},
            {'name': 'Język Niemiecki', 'color': '#8B5CF6'},
            {'name': 'Fizyka', 'color': '#F59E0B'},
            {'name': 'Chemia', 'color': '#06B6D4'},
            {'name': 'Biologia', 'color': '#84CC16'},
            {'name': 'Historia', 'color': '#F97316'},
            {'name': 'Geografia', 'color': '#14B8A6'},
            {'name': 'Informatyka', 'color': '#6366F1'},
        ]

        for subject_data in subjects:
            Subject.objects.update_or_create(
                name=subject_data['name'],
                defaults=subject_data
            )
        self.stdout.write(self.style.SUCCESS(f'Created {len(subjects)} subjects'))

        # 3. Create education levels
        levels = [
            {'name': 'Klasa 1', 'order_index': 1, 'category': 'PRIMARY'},
            {'name': 'Klasa 2', 'order_index': 2, 'category': 'PRIMARY'},
            {'name': 'Klasa 3', 'order_index': 3, 'category': 'PRIMARY'},
            {'name': 'Klasa 4', 'order_index': 4, 'category': 'PRIMARY'},
            {'name': 'Klasa 5', 'order_index': 5, 'category': 'PRIMARY'},
            {'name': 'Klasa 6', 'order_index': 6, 'category': 'PRIMARY'},
            {'name': 'Klasa 7', 'order_index': 7, 'category': 'PRIMARY'},
            {'name': 'Klasa 8', 'order_index': 8, 'category': 'PRIMARY'},
            {'name': 'Liceum 1', 'order_index': 9, 'category': 'SECONDARY'},
            {'name': 'Liceum 2', 'order_index': 10, 'category': 'SECONDARY'},
            {'name': 'Liceum 3', 'order_index': 11, 'category': 'SECONDARY'},
            {'name': 'Liceum 4', 'order_index': 12, 'category': 'SECONDARY'},
        ]

        for level_data in levels:
            Level.objects.update_or_create(
                name=level_data['name'],
                defaults=level_data
            )
        self.stdout.write(self.style.SUCCESS(f'Created {len(levels)} education levels'))

        # 4. Create default online room
        Room.objects.update_or_create(
            name='Online',
            defaults={
                'location': 'Virtual',
                'capacity': 10,
                'is_virtual': True,
                'equipment': {
                    'videoConference': True,
                    'whiteboard': True,
                    'screenShare': True,
                },
            }
        )
        self.stdout.write(self.style.SUCCESS('Created default online room'))

        self.stdout.write(self.style.SUCCESS('Production database seeded successfully!'))
```

---

## ERROR TRACKING & MONITORING (SENTRY)

### Sentry Configuration

**File**: `napiatke/sentry.py`

```python
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
import logging


def init_sentry(dsn: str, environment: str = 'production'):
    """Initialize Sentry error tracking."""

    sentry_logging = LoggingIntegration(
        level=logging.INFO,
        event_level=logging.ERROR
    )

    sentry_sdk.init(
        dsn=dsn,
        integrations=[
            DjangoIntegration(),
            CeleryIntegration(),
            RedisIntegration(),
            sentry_logging,
        ],
        traces_sample_rate=0.1,
        profiles_sample_rate=0.1,
        send_default_pii=False,
        environment=environment,

        before_send=filter_sensitive_data,
    )


def filter_sensitive_data(event, hint):
    """Filter sensitive data before sending to Sentry."""

    # Remove database credentials from error messages
    if event.get('exception'):
        for exception in event['exception'].get('values', []):
            if exception.get('value'):
                exception['value'] = exception['value'].replace(
                    exception['value'],
                    _filter_credentials(exception['value'])
                )

    # Remove request cookies and headers
    if event.get('request'):
        event['request'].pop('cookies', None)
        if event['request'].get('headers'):
            # Keep only safe headers
            safe_headers = ['Content-Type', 'Accept', 'User-Agent']
            event['request']['headers'] = {
                k: v for k, v in event['request']['headers'].items()
                if k in safe_headers
            }

    return event


def _filter_credentials(text: str) -> str:
    """Filter database and API credentials from text."""
    import re

    # Filter PostgreSQL connection strings
    text = re.sub(
        r'postgresql://[^@]+@',
        'postgresql://[FILTERED]@',
        text
    )

    # Filter Redis connection strings
    text = re.sub(
        r'redis://[^@]+@',
        'redis://[FILTERED]@',
        text
    )

    return text
```

### Health Check Endpoint

**File**: `apps/core/views.py`

```python
from django.http import JsonResponse
from django.views import View
from django.db import connection
from django.core.cache import cache


class HealthCheckView(View):
    """Health check endpoint for monitoring."""

    def get(self, request):
        health = {
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'database': 'unknown',
            'cache': 'unknown',
        }

        # Check database
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
            health['database'] = 'connected'
        except Exception as e:
            health['database'] = 'disconnected'
            health['status'] = 'unhealthy'

        # Check cache
        try:
            cache.set('health_check', 'ok', 10)
            if cache.get('health_check') == 'ok':
                health['cache'] = 'connected'
            else:
                health['cache'] = 'error'
                health['status'] = 'unhealthy'
        except Exception as e:
            health['cache'] = 'disconnected'
            health['status'] = 'unhealthy'

        status_code = 200 if health['status'] == 'healthy' else 503
        return JsonResponse(health, status=status_code)
```

---

## ANALYTICS & LOGGING

### Request Logging Middleware

**File**: `apps/core/middleware/analytics.py`

```python
import time
import logging
from django.utils import timezone

logger = logging.getLogger('analytics')


class AnalyticsMiddleware:
    """Middleware for request analytics and logging."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Start timing
        start_time = time.time()

        # Process request
        response = self.get_response(request)

        # Calculate duration
        duration = time.time() - start_time

        # Log request
        self._log_request(request, response, duration)

        return response

    def _log_request(self, request, response, duration):
        """Log request analytics."""
        # Skip health checks and static files
        if request.path in ['/api/health/', '/favicon.ico']:
            return
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            return

        log_data = {
            'timestamp': timezone.now().isoformat(),
            'method': request.method,
            'path': request.path,
            'status': response.status_code,
            'duration': f'{duration:.3f}s',
            'user_id': getattr(request.user, 'pk', None) if request.user.is_authenticated else None,
            'ip': self._get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', '')[:100],
            'htmx': bool(getattr(request, 'htmx', False)),
        }

        if duration > 1.0:
            logger.warning(f'Slow request: {log_data}')
        else:
            logger.info(f'Request: {log_data}')

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')
```

### Analytics Service

**File**: `apps/core/services/analytics.py`

```python
from django.db.models import Count, Sum, Avg
from django.utils import timezone
from datetime import timedelta
from django.core.cache import cache


class AnalyticsService:
    """Service for collecting and reporting analytics."""

    CACHE_TTL = 300  # 5 minutes

    @classmethod
    def get_dashboard_stats(cls):
        """Get main dashboard statistics."""
        cache_key = 'analytics:dashboard:stats'
        stats = cache.get(cache_key)

        if stats is None:
            from apps.accounts.models import User
            from apps.lessons.models import Lesson
            from apps.invoices.models import Invoice

            today = timezone.now().date()
            month_start = today.replace(day=1)

            stats = {
                'total_students': User.objects.filter(role='STUDENT', is_active=True).count(),
                'total_tutors': User.objects.filter(role='TUTOR', is_active=True).count(),
                'today_lessons': Lesson.objects.filter(
                    start_time__date=today,
                    status__in=['SCHEDULED', 'ONGOING', 'COMPLETED']
                ).count(),
                'monthly_revenue': Invoice.objects.filter(
                    issued_date__gte=month_start,
                    status='PAID'
                ).aggregate(total=Sum('total_amount'))['total'] or 0,
            }

            cache.set(cache_key, stats, cls.CACHE_TTL)

        return stats

    @classmethod
    def get_user_growth(cls, days=30):
        """Get user registration growth over time."""
        from apps.accounts.models import User
        from django.db.models.functions import TruncDate

        start_date = timezone.now() - timedelta(days=days)

        return User.objects.filter(
            date_joined__gte=start_date
        ).annotate(
            date=TruncDate('date_joined')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')

    @classmethod
    def get_attendance_rate(cls, start_date, end_date):
        """Calculate attendance rate for period."""
        from apps.attendance.models import Attendance
        from apps.lessons.models import Lesson

        lessons = Lesson.objects.filter(
            start_time__gte=start_date,
            start_time__lte=end_date,
            status='COMPLETED'
        )

        total = Attendance.objects.filter(lesson__in=lessons).count()
        present = Attendance.objects.filter(
            lesson__in=lessons,
            status='PRESENT'
        ).count()

        return {
            'total': total,
            'present': present,
            'rate': round((present / total) * 100, 2) if total > 0 else 0,
        }

    @classmethod
    def invalidate_cache(cls):
        """Invalidate all analytics caches."""
        cache.delete('analytics:dashboard:stats')
```

---

## AUTOMATED BACKUP CONFIGURATION

### Backup Script

**File**: `scripts/backup.sh`

```bash
#!/bin/bash
set -e

# Configuration
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d-%H%M%S)
BACKUP_FILE="napiatke-backup-$DATE.sql"
RETENTION_DAYS=30

echo "Starting database backup..."

# Create backup directory
mkdir -p $BACKUP_DIR

# Dump database
docker exec napiatke_db pg_dump -U $POSTGRES_USER $POSTGRES_DB > "$BACKUP_DIR/$BACKUP_FILE"

# Compress
gzip "$BACKUP_DIR/$BACKUP_FILE"
BACKUP_SIZE=$(du -h "$BACKUP_DIR/$BACKUP_FILE.gz" | cut -f1)

echo "Backup complete: $BACKUP_FILE.gz ($BACKUP_SIZE)"

# Upload to S3 (if configured)
if [ -n "$AWS_S3_BUCKET" ]; then
    echo "Uploading to S3..."
    aws s3 cp "$BACKUP_DIR/$BACKUP_FILE.gz" "s3://$AWS_S3_BUCKET/backups/"
    echo "Uploaded to S3"
fi

# Cleanup old backups
echo "Cleaning up old backups..."
find $BACKUP_DIR -name "*.sql.gz" -mtime +$RETENTION_DAYS -delete

# Send notification
if [ -n "$SLACK_WEBHOOK" ]; then
    curl -X POST $SLACK_WEBHOOK -H 'Content-Type: application/json' -d "{
        \"text\": \"Database backup complete: $BACKUP_FILE.gz ($BACKUP_SIZE)\"
    }"
fi

echo "Backup process finished"
```

### Celery Scheduled Tasks

**File**: `napiatke/celery.py`

```python
from celery import Celery
from celery.schedules import crontab
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'napiatke.settings.production')

app = Celery('napiatke')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Scheduled tasks
app.conf.beat_schedule = {
    # Daily backup at 2 AM
    'daily-backup': {
        'task': 'apps.core.tasks.run_backup',
        'schedule': crontab(hour=2, minute=0),
    },
    # Monthly invoices on 25th
    'monthly-invoices': {
        'task': 'apps.invoices.tasks.generate_monthly_invoices',
        'schedule': crontab(day_of_month=25, hour=0, minute=0),
    },
    # Daily reminders at 8 AM
    'daily-reminders': {
        'task': 'apps.notifications.tasks.send_daily_reminders',
        'schedule': crontab(hour=8, minute=0),
    },
    # Expire makeup lessons daily at 6 AM
    'expire-makeup-lessons': {
        'task': 'apps.cancellations.tasks.expire_makeup_lessons',
        'schedule': crontab(hour=6, minute=0),
    },
    # Cleanup old sessions weekly
    'cleanup-sessions': {
        'task': 'apps.core.tasks.cleanup_expired_sessions',
        'schedule': crontab(day_of_week=0, hour=3, minute=0),
    },
}
```

### Backup Task

**File**: `apps/core/tasks.py`

```python
import subprocess
import logging
from celery import shared_task
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task
def run_backup():
    """Run database backup task."""
    try:
        logger.info('Starting database backup...')

        result = subprocess.run(
            ['/app/scripts/backup.sh'],
            capture_output=True,
            text=True,
            check=True
        )

        logger.info(f'Backup completed: {result.stdout}')
        return {'status': 'success', 'output': result.stdout}

    except subprocess.CalledProcessError as e:
        logger.error(f'Backup failed: {e.stderr}')
        return {'status': 'failed', 'error': e.stderr}


@shared_task
def cleanup_expired_sessions():
    """Clean up expired database sessions."""
    from django.contrib.sessions.models import Session

    expired = Session.objects.filter(expire_date__lt=timezone.now())
    count = expired.count()
    expired.delete()

    logger.info(f'Cleaned up {count} expired sessions')
    return {'deleted': count}
```

---

## COMPLETION CHECKLIST

### Production Environment

- [ ] Docker Compose production configuration
- [ ] Dockerfile multi-stage build
- [ ] Nginx reverse proxy with SSL
- [ ] Production Django settings
- [ ] Environment variables documented

### Database Migration

- [ ] Migration script tested
- [ ] Seed script creates initial data
- [ ] Admin user created
- [ ] Subjects and levels populated
- [ ] Rollback procedure documented

### Error Tracking

- [ ] Sentry initialized
- [ ] Sensitive data filtered
- [ ] Error alerts configured
- [ ] Performance monitoring enabled

### Analytics

- [ ] Request logging middleware
- [ ] Dashboard statistics
- [ ] User growth tracking
- [ ] Attendance rate calculation

### Backups

- [ ] Automated daily backups
- [ ] S3 upload (optional)
- [ ] Retention policy (30 days)
- [ ] Restoration procedure tested

---

**Sprint Completion**: All 5 tasks completed and validated
**Next Sprint**: 13.2 - GO-LIVE! (Tasks 158-165)
**Status**: Production infrastructure ready
