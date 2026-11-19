"""
Base Django settings for napiatke project.
"""

from pathlib import Path

import environ


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Environment variables
env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, []),
)
environ.Env.read_env(BASE_DIR / '.env')

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG')

ALLOWED_HOSTS = env('ALLOWED_HOSTS')


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    # Third party
    'django_htmx',
    'crispy_forms',
    'crispy_tailwind',
    'django_filters',
    'django_celery_beat',
    # Local apps
    'apps.core',
    'apps.accounts',
    'apps.tutors',
    'apps.students',
    'apps.subjects',
    'apps.rooms',
    'apps.lessons',
    'apps.attendance',
    'apps.messages',
    'apps.notifications',
    'apps.cancellations',
    'apps.invoices',
    'apps.parents',
    'apps.landing',
    'apps.admin_panel',
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
                'apps.notifications.context_processors.announcements',
            ],
        },
    },
]

WSGI_APPLICATION = 'napiatke.wsgi.application'


# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# Login settings
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'accounts:login-redirect'
LOGOUT_REDIRECT_URL = 'landing:home'


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        },
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
LANGUAGE_CODE = 'pl'

TIME_ZONE = 'Europe/Warsaw'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'


# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = 'tailwind'
CRISPY_TEMPLATE_PACK = 'tailwind'


# Celery
CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Celery Beat Schedule
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    # Lessons / attendance / reports
    'send-lesson-reminders': {
        'task': 'apps.lessons.tasks.send_lesson_reminders',
        'schedule': crontab(hour=18, minute=0),
    },
    'check-attendance-alerts': {
        'task': 'apps.attendance.tasks.check_attendance_alerts',
        'schedule': crontab(hour=8, minute=0),
    },
    'generate-monthly-reports': {
        'task': 'apps.attendance.tasks.generate_monthly_reports_task',
        'schedule': crontab(day_of_month=1, hour=6, minute=0),
        'args': (None,),  # previous month
    },
    'send-weekly-summaries': {
        'task': 'apps.notifications.tasks.send_weekly_summaries_task',
        'schedule': crontab(day_of_week=0, hour=18, minute=0),
    },
    # Makeup lessons (30-day window)
    'expire-makeup-lessons': {
        'task': 'apps.cancellations.tasks.expire_makeup_lessons',
        'schedule': crontab(hour=0, minute=5),
    },
    'send-makeup-warnings': {
        'task': 'apps.cancellations.tasks.send_makeup_expiration_warnings',
        'schedule': crontab(hour=8, minute=15),
    },
    'cleanup-expired-notifications': {
        'task': 'apps.notifications.tasks.cleanup_expired_notifications',
        'schedule': crontab(hour=3, minute=0),
    },
    # Invoices
    'monthly-billing': {
        'task': 'apps.invoices.tasks.monthly_billing_task',
        'schedule': crontab(day_of_month=25, hour=0, minute=0),
    },
    'check-overdue-invoices': {
        'task': 'apps.invoices.tasks.check_overdue_invoices_task',
        'schedule': crontab(hour=8, minute=0),  # Daily at 8 AM
    },
}


# Email
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@napiatke.pl')


# Session
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 7200  # 2 hours
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
