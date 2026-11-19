"""Rate limiting helpers (django-ratelimit).

Behind nginx every request has REMOTE_ADDR=127.0.0.1, so the client IP is
taken from X-Real-IP, which the nginx config sets (and overwrites) from
$remote_addr.
"""

from functools import wraps

from django.http import HttpResponse
from django_ratelimit.core import is_ratelimited


def client_ip(group, request):
    return request.META.get('HTTP_X_REAL_IP') or request.META.get('REMOTE_ADDR', '')


def limit_posts(rate, group):
    """Wrap a view callable: limit POSTs per client IP; 429 before the view runs."""

    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            if request.method == 'POST' and is_ratelimited(
                request, group=group, key=client_ip, rate=rate, method='POST', increment=True
            ):
                return HttpResponse(
                    'Zbyt wiele prób. Spróbuj ponownie za kilka minut.', status=429
                )
            return view(request, *args, **kwargs)

        return wrapper

    return decorator
