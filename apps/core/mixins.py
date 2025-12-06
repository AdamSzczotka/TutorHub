from django.contrib.auth.mixins import UserPassesTestMixin


class HTMXMixin:
    """Mixin for HTMX-aware views."""

    partial_template_name: str | None = None

    def get_template_names(self):
        """Return partial template for HTMX requests."""
        if getattr(self.request, 'htmx', False) and self.partial_template_name:
            return [self.partial_template_name]
        return super().get_template_names()


class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin requiring admin role."""

    def test_func(self) -> bool:
        """Check if user is admin."""
        return self.request.user.is_authenticated and self.request.user.is_admin


class TutorRequiredMixin(UserPassesTestMixin):
    """Mixin requiring tutor or admin role."""

    def test_func(self) -> bool:
        """Check if user is tutor or admin."""
        user = self.request.user
        return user.is_authenticated and (user.is_tutor or user.is_admin)


class StudentRequiredMixin(UserPassesTestMixin):
    """Mixin requiring student or admin role."""

    def test_func(self) -> bool:
        """Check if user is student or admin."""
        user = self.request.user
        return user.is_authenticated and (user.is_student or user.is_admin)
