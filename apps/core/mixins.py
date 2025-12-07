"""Mixins for views in napiatke project."""

from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import PermissionDenied

from apps.core.permissions import Permission, has_permission


class HTMXMixin:
    """Mixin for HTMX-aware views."""

    partial_template_name: str | None = None

    def get_template_names(self):
        """Return partial template for HTMX requests."""
        if getattr(self.request, 'htmx', False) and self.partial_template_name:
            return [self.partial_template_name]
        return super().get_template_names()


class PermissionRequiredMixin(AccessMixin):
    """Mixin that checks for specific permissions.

    Redirects to login if not authenticated, raises 403 if no permission.
    """

    required_permissions: list[Permission] = []

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        for permission in self.required_permissions:
            if not has_permission(request.user, permission):
                raise PermissionDenied('Brak uprawnień do tej akcji.')
        return super().dispatch(request, *args, **kwargs)


class AdminRequiredMixin(AccessMixin):
    """Mixin requiring admin role.

    Redirects to login if not authenticated, raises 403 if not admin.
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.is_admin:
            raise PermissionDenied('Wymagane uprawnienia administratora.')
        return super().dispatch(request, *args, **kwargs)


class TutorRequiredMixin(AccessMixin):
    """Mixin requiring tutor or admin role.

    Redirects to login if not authenticated, raises 403 if not tutor/admin.
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not (request.user.is_tutor or request.user.is_admin):
            raise PermissionDenied('Wymagane uprawnienia korepetytora.')
        return super().dispatch(request, *args, **kwargs)


class StudentRequiredMixin(AccessMixin):
    """Mixin requiring student or admin role.

    Redirects to login if not authenticated, raises 403 if not student/admin.
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not (request.user.is_student or request.user.is_admin):
            raise PermissionDenied('Wymagane uprawnienia ucznia.')
        return super().dispatch(request, *args, **kwargs)
