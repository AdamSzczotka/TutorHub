# Phase 11 - Sprint 11.1: Performance Optimization (Django)

## Tasks 133-137: Performance & Optimization

> **Duration**: Week 15 (First half of Phase 11)
> **Goal**: Optimize application performance, implement caching strategies, database optimization
> **Dependencies**: Phase 1-10 completed (All features operational)

---

## SPRINT OVERVIEW

| Task ID | Description                           | Priority | Dependencies      |
| ------- | ------------------------------------- | -------- | ----------------- |
| 133     | Static files & image optimization     | Critical | Phase 10 complete |
| 134     | Django query optimization             | Critical | Task 133          |
| 135     | Redis caching implementation          | Critical | Task 134          |
| 136     | HTMX response optimization            | High     | Task 135          |
| 137     | Monitoring & profiling setup          | High     | Task 136          |

---

## STATIC FILES & IMAGE OPTIMIZATION

### WhiteNoise Configuration

**File**: `napiatke/settings/production.py`

```python
# Static files optimization with WhiteNoise

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Add after security
    # ... other middleware
]

# WhiteNoise settings
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Cache headers
WHITENOISE_MAX_AGE = 31536000  # 1 year for versioned files
```

### Image Optimization with Pillow

**File**: `apps/core/utils/images.py`

```python
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys


def optimize_image(image_file, max_size=(1920, 1080), quality=85):
    """
    Optimize uploaded image:
    - Convert to WebP format
    - Resize if too large
    - Compress for web
    """
    img = Image.open(image_file)

    # Convert RGBA to RGB if needed
    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')

    # Resize if needed
    if img.width > max_size[0] or img.height > max_size[1]:
        img.thumbnail(max_size, Image.Resampling.LANCZOS)

    # Save as WebP
    output = BytesIO()
    img.save(output, format='WEBP', quality=quality, optimize=True)
    output.seek(0)

    return InMemoryUploadedFile(
        output,
        'ImageField',
        f"{image_file.name.rsplit('.', 1)[0]}.webp",
        'image/webp',
        sys.getsizeof(output),
        None
    )


def generate_thumbnail(image_file, size=(300, 300)):
    """Generate thumbnail for image."""
    img = Image.open(image_file)

    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')

    img.thumbnail(size, Image.Resampling.LANCZOS)

    output = BytesIO()
    img.save(output, format='WEBP', quality=80)
    output.seek(0)

    return output


def generate_blur_placeholder(image_file, size=(20, 20)):
    """Generate tiny blur placeholder for lazy loading."""
    img = Image.open(image_file)

    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')

    img.thumbnail(size, Image.Resampling.LANCZOS)

    output = BytesIO()
    img.save(output, format='WEBP', quality=20)
    output.seek(0)

    import base64
    return f"data:image/webp;base64,{base64.b64encode(output.getvalue()).decode()}"
```

### Lazy Loading Image Template Tag

**File**: `apps/core/templatetags/image_tags.py`

```python
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def lazy_image(src, alt, width=None, height=None, css_class=''):
    """
    Render lazy-loaded image with blur placeholder.

    Usage: {% lazy_image image.url "Alt text" width=400 height=300 %}
    """
    placeholder = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1 1'%3E%3C/svg%3E"

    attrs = [
        f'src="{placeholder}"',
        f'data-src="{src}"',
        f'alt="{alt}"',
        'loading="lazy"',
        f'class="lazy-image {css_class}"',
    ]

    if width:
        attrs.append(f'width="{width}"')
    if height:
        attrs.append(f'height="{height}"')

    return mark_safe(f'<img {" ".join(attrs)}>')


@register.simple_tag
def responsive_image(image, alt, sizes='100vw', css_class=''):
    """
    Render responsive image with srcset.
    """
    # Generate srcset for different sizes
    srcset_sizes = [320, 640, 960, 1280, 1920]
    srcset_parts = []

    for size in srcset_sizes:
        # Assuming image has get_thumbnail method
        thumb_url = f"{image.url}?w={size}"
        srcset_parts.append(f"{thumb_url} {size}w")

    srcset = ", ".join(srcset_parts)

    return mark_safe(f'''
        <img
            src="{image.url}"
            srcset="{srcset}"
            sizes="{sizes}"
            alt="{alt}"
            loading="lazy"
            class="{css_class}"
        >
    ''')
```

### Alpine.js Lazy Loading Script

**File**: `static/js/lazy-images.js`

```javascript
// Lazy loading with Intersection Observer
document.addEventListener('alpine:init', () => {
    Alpine.directive('lazy-src', (el, { expression }) => {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    el.src = el.dataset.src || expression;
                    el.classList.add('loaded');
                    observer.unobserve(el);
                }
            });
        }, {
            rootMargin: '50px'
        });

        observer.observe(el);
    });
});

// Apply to all lazy images
document.addEventListener('DOMContentLoaded', () => {
    const lazyImages = document.querySelectorAll('.lazy-image');

    if ('IntersectionObserver' in window) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.remove('lazy-image');
                    img.classList.add('loaded');
                    observer.unobserve(img);
                }
            });
        });

        lazyImages.forEach(img => observer.observe(img));
    } else {
        // Fallback for older browsers
        lazyImages.forEach(img => {
            img.src = img.dataset.src;
        });
    }
});
```

---

## DATABASE QUERY OPTIMIZATION

### Optimized QuerySets

**File**: `apps/core/querysets.py`

```python
from django.db import models
from django.db.models import Count, Prefetch, Q, Sum, Avg


class OptimizedLessonQuerySet(models.QuerySet):
    """Optimized queryset for Lesson model."""

    def with_related(self):
        """Include all commonly needed related data."""
        return self.select_related(
            'tutor',
            'tutor__tutor_profile',
            'subject',
            'room'
        ).prefetch_related(
            Prefetch(
                'lessonstudent_set',
                queryset=models.LessonStudent.objects.select_related(
                    'student',
                    'student__student_profile'
                )
            )
        )

    def upcoming(self):
        """Get upcoming lessons."""
        from django.utils import timezone
        return self.filter(
            start_time__gt=timezone.now(),
            status='SCHEDULED'
        ).order_by('start_time')

    def for_calendar(self, start, end):
        """Optimized query for calendar view."""
        return self.filter(
            start_time__gte=start,
            end_time__lte=end
        ).select_related(
            'tutor',
            'subject',
            'room'
        ).only(
            'id', 'title', 'start_time', 'end_time', 'status',
            'tutor__first_name', 'tutor__last_name',
            'subject__name', 'subject__color',
            'room__name'
        )

    def with_student_counts(self):
        """Annotate with student counts."""
        return self.annotate(
            student_count=Count('lessonstudent'),
            present_count=Count(
                'lessonstudent',
                filter=Q(lessonstudent__attendance__status='PRESENT')
            )
        )


class OptimizedStudentQuerySet(models.QuerySet):
    """Optimized queryset for User (student) model."""

    def active_students(self):
        """Get active students with profiles."""
        return self.filter(
            role='STUDENT',
            is_active=True
        ).select_related('student_profile')

    def with_lesson_stats(self):
        """Include lesson statistics."""
        return self.annotate(
            total_lessons=Count('lessonstudent'),
            completed_lessons=Count(
                'lessonstudent',
                filter=Q(lessonstudent__lesson__status='COMPLETED')
            ),
            attendance_rate=Avg(
                models.Case(
                    models.When(
                        lessonstudent__attendance__status='PRESENT',
                        then=1
                    ),
                    default=0,
                    output_field=models.FloatField()
                )
            ) * 100
        )

    def for_list(self):
        """Optimized for list views."""
        return self.select_related('student_profile').only(
            'id', 'first_name', 'last_name', 'email', 'is_active',
            'student_profile__class_name'
        )
```

### Database Indexes

**File**: `apps/lessons/models.py` (add indexes)

```python
from django.db import models


class Lesson(models.Model):
    """Lesson model with optimized indexes."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    title = models.CharField(max_length=255)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=LessonStatus.choices)
    tutor = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    subject = models.ForeignKey('subjects.Subject', on_delete=models.CASCADE)
    room = models.ForeignKey('rooms.Room', on_delete=models.SET_NULL, null=True)

    class Meta:
        db_table = 'lessons'
        indexes = [
            # Calendar queries
            models.Index(fields=['start_time', 'end_time']),
            # Status + time queries
            models.Index(fields=['status', 'start_time']),
            # Tutor schedule
            models.Index(fields=['tutor', 'start_time']),
            # Room availability
            models.Index(fields=['room', 'start_time', 'end_time']),
            # Upcoming lessons
            models.Index(
                fields=['status', 'start_time'],
                name='upcoming_lessons_idx',
                condition=Q(status='SCHEDULED')
            ),
        ]


class LessonStudent(models.Model):
    """M2M relationship with attendance."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    student = models.ForeignKey('accounts.User', on_delete=models.CASCADE)

    class Meta:
        db_table = 'lesson_students'
        unique_together = ['lesson', 'student']
        indexes = [
            models.Index(fields=['student', 'lesson']),
        ]
```

### Query Debugging Middleware

**File**: `apps/core/middleware/query_debug.py`

```python
import logging
import time
from django.db import connection, reset_queries
from django.conf import settings

logger = logging.getLogger('django.db')


class QueryCountMiddleware:
    """
    Middleware to log slow queries and query counts.
    Only active in DEBUG mode.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not settings.DEBUG:
            return self.get_response(request)

        reset_queries()
        start_time = time.time()

        response = self.get_response(request)

        total_time = time.time() - start_time
        queries = connection.queries

        # Log if too many queries or slow response
        if len(queries) > 20:
            logger.warning(
                f'High query count: {len(queries)} queries for {request.path}'
            )

        if total_time > 0.5:
            logger.warning(
                f'Slow request: {total_time:.2f}s for {request.path}'
            )

        # Find slow individual queries
        slow_queries = [q for q in queries if float(q['time']) > 0.1]
        for query in slow_queries:
            logger.warning(f'Slow query ({query["time"]}s): {query["sql"][:200]}')

        # Add debug header
        response['X-Query-Count'] = str(len(queries))
        response['X-Response-Time'] = f'{total_time:.3f}s'

        return response
```

---

## REDIS CACHING IMPLEMENTATION

### Redis Configuration

**File**: `napiatke/settings/base.py`

```python
# Redis cache configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': env('REDIS_URL', default='redis://localhost:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'napiatke',
        'TIMEOUT': 300,  # 5 minutes default
    }
}

# Session cache
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# Cache timeouts
CACHE_TIMEOUTS = {
    'static': 3600,      # 1 hour for static data (subjects, levels)
    'user': 300,         # 5 minutes for user data
    'dashboard': 60,     # 1 minute for dashboard stats
    'calendar': 120,     # 2 minutes for calendar events
}
```

### Cache Service

**File**: `apps/core/services/cache.py`

```python
from django.core.cache import cache
from django.conf import settings
from functools import wraps
import hashlib
import json


class CacheService:
    """Centralized caching service."""

    @staticmethod
    def get_key(*args, **kwargs):
        """Generate cache key from arguments."""
        key_data = json.dumps({'args': args, 'kwargs': kwargs}, sort_keys=True)
        return hashlib.md5(key_data.encode()).hexdigest()

    @classmethod
    def get(cls, key, default=None):
        """Get value from cache."""
        return cache.get(key, default)

    @classmethod
    def set(cls, key, value, timeout=None):
        """Set value in cache."""
        timeout = timeout or settings.CACHES['default']['TIMEOUT']
        cache.set(key, value, timeout)

    @classmethod
    def delete(cls, key):
        """Delete value from cache."""
        cache.delete(key)

    @classmethod
    def delete_pattern(cls, pattern):
        """Delete all keys matching pattern."""
        from django_redis import get_redis_connection
        redis = get_redis_connection('default')

        full_pattern = f"{settings.CACHES['default']['KEY_PREFIX']}:{pattern}*"
        keys = redis.keys(full_pattern)

        if keys:
            redis.delete(*keys)

    @classmethod
    def invalidate_user(cls, user_id):
        """Invalidate all cache for user."""
        cls.delete_pattern(f'user:{user_id}')

    @classmethod
    def invalidate_lesson(cls, lesson_id):
        """Invalidate cache related to lesson."""
        cls.delete_pattern(f'lesson:{lesson_id}')
        cls.delete_pattern('calendar:')
        cls.delete_pattern('dashboard:')


def cached(timeout=300, key_prefix=''):
    """
    Decorator for caching function results.

    Usage:
        @cached(timeout=600, key_prefix='subjects')
        def get_subjects():
            return Subject.objects.all()
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{CacheService.get_key(*args, **kwargs)}"

            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)

            return result
        return wrapper
    return decorator


def cached_method(timeout=300, key_prefix=''):
    """
    Decorator for caching instance method results.
    Includes instance ID in cache key.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            instance_key = getattr(self, 'pk', id(self))
            cache_key = f"{key_prefix}:{instance_key}:{CacheService.get_key(*args, **kwargs)}"

            result = cache.get(cache_key)
            if result is not None:
                return result

            result = func(self, *args, **kwargs)
            cache.set(cache_key, result, timeout)

            return result
        return wrapper
    return decorator
```

### Cached Views

**File**: `apps/core/views/cached.py`

```python
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.conf import settings


class CachedTemplateMixin:
    """Mixin for caching template views."""

    cache_timeout = 300  # 5 minutes default

    @method_decorator(cache_page(cache_timeout))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


class VaryCacheMixin:
    """
    Mixin that varies cache by user.
    For personalized pages that still benefit from caching.
    """

    def get_cache_key(self):
        user = self.request.user
        if user.is_authenticated:
            return f"user:{user.pk}"
        return "anonymous"

    def dispatch(self, request, *args, **kwargs):
        from django.core.cache import cache

        cache_key = f"view:{self.get_cache_key()}:{request.path}"
        response = cache.get(cache_key)

        if response is None:
            response = super().dispatch(request, *args, **kwargs)
            if hasattr(response, 'render'):
                response.render()
            cache.set(cache_key, response, self.cache_timeout)

        return response
```

### Dashboard Caching Example

**File**: `apps/admin_panel/services.py`

```python
from apps.core.services.cache import cached, CacheService
from django.conf import settings


class DashboardService:
    """Dashboard statistics with caching."""

    @classmethod
    @cached(timeout=settings.CACHE_TIMEOUTS['dashboard'], key_prefix='dashboard:stats')
    def get_global_stats(cls):
        """Get global statistics (cached)."""
        from apps.lessons.models import Lesson
        from apps.accounts.models import User
        from apps.invoices.models import Invoice
        from django.utils import timezone
        from django.db.models import Count, Sum

        today = timezone.now().date()
        month_start = today.replace(day=1)

        return {
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

    @classmethod
    def get_user_stats(cls, user):
        """Get user-specific stats (shorter cache)."""
        cache_key = f"dashboard:user:{user.pk}"
        stats = CacheService.get(cache_key)

        if stats is None:
            from apps.lessons.models import LessonStudent
            from django.utils import timezone

            today = timezone.now()

            if user.role == 'TUTOR':
                stats = cls._get_tutor_stats(user)
            elif user.role == 'STUDENT':
                stats = cls._get_student_stats(user)
            else:
                stats = cls._get_admin_stats()

            CacheService.set(cache_key, stats, settings.CACHE_TIMEOUTS['user'])

        return stats

    @classmethod
    def invalidate_dashboard(cls):
        """Invalidate all dashboard caches."""
        CacheService.delete_pattern('dashboard:')
```

---

## HTMX RESPONSE OPTIMIZATION

### HTMX Response Middleware

**File**: `apps/core/middleware/htmx.py`

```python
from django.utils.deprecation import MiddlewareMixin


class HTMXOptimizationMiddleware(MiddlewareMixin):
    """Optimize responses for HTMX requests."""

    def process_response(self, request, response):
        # Skip non-HTMX requests
        if not getattr(request, 'htmx', False):
            return response

        # Add cache headers for HTMX responses
        if request.method == 'GET':
            # Short cache for HTMX partials
            response['Cache-Control'] = 'private, max-age=60'

        # Compress small responses inline
        if len(response.content) < 1024:
            response['Content-Encoding'] = 'identity'

        return response
```

### Optimized HTMX Partials

**File**: `apps/core/mixins.py` (enhanced)

```python
from django.http import HttpResponse
from django.template.loader import render_to_string


class OptimizedHTMXMixin:
    """
    Optimized mixin for HTMX views.
    Minimizes response size and adds caching headers.
    """

    partial_template_name = None
    htmx_cache_timeout = 60

    def get_template_names(self):
        if self.request.htmx and self.partial_template_name:
            return [self.partial_template_name]
        return super().get_template_names()

    def render_to_response(self, context, **response_kwargs):
        response = super().render_to_response(context, **response_kwargs)

        if self.request.htmx:
            # Add HTMX-specific headers
            response['HX-Push-Url'] = 'false'

            # Minify HTML for HTMX responses
            if hasattr(response, 'content'):
                response.content = self._minify_html(response.content)

        return response

    def _minify_html(self, content):
        """Remove extra whitespace from HTML."""
        import re
        if isinstance(content, bytes):
            content = content.decode('utf-8')

        # Remove multiple whitespaces
        content = re.sub(r'\s+', ' ', content)
        # Remove whitespace between tags
        content = re.sub(r'>\s+<', '><', content)

        return content.encode('utf-8')


class HTMXStreamingMixin:
    """
    Mixin for streaming large HTMX responses.
    Useful for tables with many rows.
    """

    streaming_chunk_size = 50

    def render_streaming_response(self, queryset, item_template):
        """
        Stream items in chunks for better perceived performance.
        """
        def generate():
            for i, item in enumerate(queryset):
                html = render_to_string(item_template, {'item': item})
                yield html

                # Add progress indicator periodically
                if i > 0 and i % self.streaming_chunk_size == 0:
                    yield f'<!-- chunk {i} -->'

        from django.http import StreamingHttpResponse
        return StreamingHttpResponse(generate(), content_type='text/html')
```

### HTMX Partial Response Caching

**File**: `apps/core/decorators.py`

```python
from functools import wraps
from django.core.cache import cache
from django.http import HttpResponse


def cache_htmx_partial(timeout=60, vary_on_user=True):
    """
    Cache HTMX partial responses.

    Usage:
        @cache_htmx_partial(timeout=120)
        def my_partial_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Only cache GET requests
            if request.method != 'GET':
                return view_func(request, *args, **kwargs)

            # Generate cache key
            cache_key = f"htmx:{request.path}"
            if vary_on_user and request.user.is_authenticated:
                cache_key += f":user:{request.user.pk}"

            # Add query params to key
            if request.GET:
                import hashlib
                params_hash = hashlib.md5(
                    request.GET.urlencode().encode()
                ).hexdigest()[:8]
                cache_key += f":params:{params_hash}"

            # Try cache
            cached_response = cache.get(cache_key)
            if cached_response:
                return HttpResponse(
                    cached_response,
                    content_type='text/html',
                    headers={'X-Cache': 'HIT'}
                )

            # Execute view
            response = view_func(request, *args, **kwargs)

            # Cache successful responses
            if response.status_code == 200:
                cache.set(cache_key, response.content, timeout)
                response['X-Cache'] = 'MISS'

            return response
        return wrapper
    return decorator
```

---

## MONITORING & PROFILING

### Django Debug Toolbar Configuration

**File**: `napiatke/settings/development.py`

```python
# Django Debug Toolbar
INSTALLED_APPS += ['debug_toolbar']

MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
] + MIDDLEWARE

INTERNAL_IPS = ['127.0.0.1']

DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': lambda request: DEBUG,
    'RESULTS_CACHE_SIZE': 100,
    'SQL_WARNING_THRESHOLD': 100,  # ms
}

DEBUG_TOOLBAR_PANELS = [
    'debug_toolbar.panels.history.HistoryPanel',
    'debug_toolbar.panels.versions.VersionsPanel',
    'debug_toolbar.panels.timer.TimerPanel',
    'debug_toolbar.panels.settings.SettingsPanel',
    'debug_toolbar.panels.headers.HeadersPanel',
    'debug_toolbar.panels.request.RequestPanel',
    'debug_toolbar.panels.sql.SQLPanel',
    'debug_toolbar.panels.staticfiles.StaticFilesPanel',
    'debug_toolbar.panels.templates.TemplatesPanel',
    'debug_toolbar.panels.cache.CachePanel',
    'debug_toolbar.panels.signals.SignalsPanel',
    'debug_toolbar.panels.redirects.RedirectsPanel',
    'debug_toolbar.panels.profiling.ProfilingPanel',
]
```

### Sentry Configuration

**File**: `napiatke/settings/production.py`

```python
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.redis import RedisIntegration

sentry_sdk.init(
    dsn=env('SENTRY_DSN'),
    integrations=[
        DjangoIntegration(),
        CeleryIntegration(),
        RedisIntegration(),
    ],
    traces_sample_rate=0.1,  # 10% of requests for performance monitoring
    profiles_sample_rate=0.1,  # 10% for profiling
    send_default_pii=False,
    environment=env('ENVIRONMENT', default='production'),
)
```

### Performance Logging

**File**: `apps/core/middleware/performance.py`

```python
import time
import logging
from django.conf import settings

logger = logging.getLogger('performance')


class PerformanceLoggingMiddleware:
    """Log performance metrics for all requests."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.slow_request_threshold = getattr(
            settings, 'SLOW_REQUEST_THRESHOLD', 1.0
        )

    def __call__(self, request):
        start_time = time.time()

        response = self.get_response(request)

        duration = time.time() - start_time

        # Log performance data
        log_data = {
            'method': request.method,
            'path': request.path,
            'status': response.status_code,
            'duration': f'{duration:.3f}s',
            'user': request.user.pk if request.user.is_authenticated else None,
            'htmx': bool(getattr(request, 'htmx', False)),
        }

        if duration > self.slow_request_threshold:
            logger.warning(f'Slow request: {log_data}')
        else:
            logger.info(f'Request: {log_data}')

        # Add timing header
        response['Server-Timing'] = f'total;dur={duration * 1000:.0f}'

        return response
```

### Cache Statistics View

**File**: `apps/admin_panel/views/cache_stats.py`

```python
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.core.mixins import AdminRequiredMixin


class CacheStatsView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    """View cache statistics for admins."""
    template_name = 'admin_panel/cache_stats.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        from django_redis import get_redis_connection
        redis = get_redis_connection('default')

        # Get cache info
        info = redis.info()

        context['cache_stats'] = {
            'used_memory': info.get('used_memory_human', 'N/A'),
            'total_keys': redis.dbsize(),
            'hits': info.get('keyspace_hits', 0),
            'misses': info.get('keyspace_misses', 0),
            'hit_rate': self._calculate_hit_rate(info),
            'connected_clients': info.get('connected_clients', 0),
        }

        # Get key patterns
        from django.conf import settings
        prefix = settings.CACHES['default']['KEY_PREFIX']

        patterns = ['dashboard:', 'user:', 'calendar:', 'lesson:']
        context['key_counts'] = {}

        for pattern in patterns:
            keys = redis.keys(f'{prefix}:{pattern}*')
            context['key_counts'][pattern] = len(keys)

        return context

    def _calculate_hit_rate(self, info):
        hits = info.get('keyspace_hits', 0)
        misses = info.get('keyspace_misses', 0)
        total = hits + misses

        if total == 0:
            return 0

        return round((hits / total) * 100, 2)
```

---

## COMPLETION CHECKLIST

### Technical Validation

- [ ] WhiteNoise serving static files with compression
- [ ] Images optimized and converted to WebP
- [ ] Lazy loading implemented for images
- [ ] Database queries optimized (select_related, prefetch_related)
- [ ] Database indexes created
- [ ] Redis caching implemented
- [ ] HTMX responses optimized
- [ ] Django Debug Toolbar configured (dev)
- [ ] Sentry monitoring configured (prod)

### Performance Metrics

- [ ] Page load time <2s on 3G
- [ ] TTFB <500ms
- [ ] Database queries per page <20
- [ ] Cache hit rate >70% for static data
- [ ] No N+1 query issues
- [ ] Image size reduced by >50%

### Monitoring

- [ ] Performance logging active
- [ ] Slow query detection working
- [ ] Cache statistics available
- [ ] Error tracking configured

---

**Sprint Completion**: All 5 tasks completed and validated
**Next Sprint**: 11.2 - Security Hardening
**Integration**: Performance optimizations ready for production
