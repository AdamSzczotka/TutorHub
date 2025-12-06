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


def htmx_trigger(event: str, data: str | None = None) -> HttpResponse:
    """Return HTMX trigger response."""
    response = HttpResponse()
    if data:
        response['HX-Trigger'] = f'{{"{event}": "{data}"}}'
    else:
        response['HX-Trigger'] = event
    return response
