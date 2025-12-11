"""
Development settings for napiatke project.
"""

from .base import *  # noqa: F401, F403

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Additional apps for development
INSTALLED_APPS += [  # noqa: F405
    'debug_toolbar',
    'django_extensions',
]

# Debug toolbar middleware
MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')  # noqa: F405

# Internal IPs for debug toolbar
INTERNAL_IPS = ['127.0.0.1']

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME', default='napiatke'),  # noqa: F405
        'USER': env('DB_USER', default='admin'),  # noqa: F405
        'PASSWORD': env('DB_PASSWORD', default='admin123'),  # noqa: F405
        'HOST': env('DB_HOST', default='localhost'),  # noqa: F405
        'PORT': env('DB_PORT', default='5432'),  # noqa: F405
    }
}

# Cache (Redis)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': env('REDIS_URL', default='redis://localhost:6379/0'),  # noqa: F405
    }
}

# Email - Gmail SMTP
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST', default='smtp.gmail.com')  # noqa: F405
EMAIL_PORT = env.int('EMAIL_PORT', default=587)  # noqa: F405
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)  # noqa: F405
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')  # noqa: F405
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')  # noqa: F405
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@napiatke.pl')  # noqa: F405

# Celery - run tasks synchronously in development (no need for worker)
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
