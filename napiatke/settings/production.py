"""
Production settings for napiatke project.
"""

from urllib.parse import urlparse

from .base import *  # noqa: F401, F403

DEBUG = False

SITE_URL = env('SITE_URL', default='https://tutorhub.adamszczotka.dev')  # noqa: F405

# Comma-separated list. '*' is ignored (it enables Host-header poisoning of
# password-reset links); if nothing else is configured, fall back to the
# SITE_URL host so the site keeps working when the env still says '*'.
ALLOWED_HOSTS = [
    h for h in env.list('ALLOWED_HOSTS', default=[]) if h and h != '*'  # noqa: F405
] or [urlparse(SITE_URL).hostname]
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[SITE_URL])  # noqa: F405

# nginx terminates TLS and sets X-Forwarded-Proto
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Database
DATABASES = {
    'default': env.db('DATABASE_URL')  # noqa: F405
}

# Security
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Static files: served by nginx from STATIC_ROOT (collectstatic). Default
# storage on purpose - a manifest storage turns any missing static file
# into a 500 for the whole page.

# Cache (Redis)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': env('REDIS_URL'),  # noqa: F405
    }
}

# Email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST', default='smtp.resend.com')  # noqa: F405
EMAIL_PORT = env.int('EMAIL_PORT', default=587)  # noqa: F405
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')  # noqa: F405
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')  # noqa: F405
EMAIL_USE_TLS = True

# Sentry
SENTRY_DSN = env('SENTRY_DSN', default='')  # noqa: F405
if SENTRY_DSN:
    import sentry_sdk

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        traces_sample_rate=0.1,
    )

