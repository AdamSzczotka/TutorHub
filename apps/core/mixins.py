"""Mixins for views in napiatke project."""

from django.contrib.auth.mixins import UserPassesTestMixin
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


class PermissionRequiredMixin(UserPassesTestMixin):
    """Mixin that checks for specific permissions."""

    required_permissions: list[Permission] = []

    def test_func(self) -> bool:
        """Check if user has all required permissions."""
        if not self.request.user.is_authenticated:
            return False

        for permission in self.required_permissions:
            if not has_permission(self.request.user, permission):
                return False
        return True

    def handle_no_permission(self):
        """Handle permission denied."""
        raise PermissionDenied('Brak uprawnień do tej akcji.')


class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin requiring admin role."""

    def test_func(self) -> bool:
        """Check if user is admin."""
        return self.request.user.is_authenticated and self.request.user.is_admin

    def handle_no_permission(self):
        """Handle permission denied."""
        raise PermissionDenied('Wymagane uprawnienia administratora.')


class TutorRequiredMixin(UserPassesTestMixin):
    """Mixin requiring tutor or admin role."""

    def test_func(self) -> bool:
        """Check if user is tutor or admin."""
        user = self.request.user
        return user.is_authenticated and (user.is_tutor or user.is_admin)

    def handle_no_permission(self):
        """Handle permission denied."""
        raise PermissionDenied('Wymagane uprawnienia korepetytora.')


class StudentRequiredMixin(UserPassesTestMixin):
    """Mixin requiring student or admin role."""

    def test_func(self) -> bool:
        """Check if user is student or admin."""
        user = self.request.user
        return user.is_authenticated and (user.is_student or user.is_admin)

    def handle_no_permission(self):
        """Handle permission denied."""
        raise PermissionDenied('Wymagane uprawnienia ucznia.')
