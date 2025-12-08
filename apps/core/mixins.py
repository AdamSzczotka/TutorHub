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


class ParentAccessMixin(AccessMixin):
    """Mixin that verifies parent access to student data.

    Parent access is granted when:
    1. User is admin (can access all)
    2. User is the student themselves
    3. User's email matches student's parent_email (shared access)
    """

    def get_student(self):
        """Get the student object for parent access validation."""
        from django.shortcuts import get_object_or_404

        from apps.accounts.models import User

        student_id = self.kwargs.get('student_id') or self.request.GET.get('student_id')
        if not student_id:
            # Default to current user if they are a student
            if self.request.user.is_student:
                return self.request.user
            return None
        return get_object_or_404(User, pk=student_id, role='student')

    def has_parent_access(self, student) -> bool:
        """Check if current user has parent access to student data."""
        user = self.request.user

        if student is None:
            return False

        # Admin can access all
        if user.is_admin:
            return True

        # Student can access their own data
        if user.id == student.id:
            return True

        # Check parent email match (for shared parent/student access)
        try:
            parent_email = student.student_profile.parent_email
            if parent_email and user.email == parent_email:
                return True
        except Exception:
            pass

        return False

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        student = self.get_student()
        if not self.has_parent_access(student):
            raise PermissionDenied('Brak dostepu do danych tego ucznia')

        # Store student in request for use in views
        request.current_student = student
        return super().dispatch(request, *args, **kwargs)


class ParentRequiredMixin(AccessMixin):
    """Mixin for views that require parent role.

    Parents can be identified by:
    1. Having a student account with parent access enabled
    2. Email matching a student's parent_email field
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        # Check if user has any children (students linked to them)
        has_children = self._get_children(request.user).exists()

        if not has_children and not request.user.is_admin:
            raise PermissionDenied('Brak dostepu do portalu rodzica')

        return super().dispatch(request, *args, **kwargs)

    def _get_children(self, user):
        """Get students this user has parent access to."""
        from apps.accounts.models import User

        # If user is a student, return themselves
        if user.is_student:
            return User.objects.filter(pk=user.pk)

        # Check for students where this user's email is parent_email
        return User.objects.filter(
            role='student', student_profile__parent_email=user.email
        )
