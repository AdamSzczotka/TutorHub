"""
Production settings for napiatke project.
"""

from .base import *  # noqa: F401, F403

DEBUG = False

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')  # noqa: F405

# Database
DATABASES = {
    'default': env.db('DATABASE_URL')  # noqa: F405
}

# Security
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Static files
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

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
