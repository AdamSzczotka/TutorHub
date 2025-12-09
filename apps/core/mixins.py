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
    3. User has role='parent' and has ParentAccess to the student
    """

    def get_student(self):
        """Get the student object for parent access validation."""
        from django.shortcuts import get_object_or_404

        from apps.accounts.models import User

        student_id = self.kwargs.get('student_id') or self.request.GET.get('student_id')
        if not student_id:
            # For parents, get first child
            if self.request.user.is_parent:
                from apps.accounts.models import ParentAccess

                first_access = ParentAccess.objects.filter(
                    parent=self.request.user,
                    is_active=True,
                ).select_related('student').first()
                if first_access:
                    return first_access.student
            # Default to current user if they are a student
            elif self.request.user.is_student:
                return self.request.user
            return None
        return get_object_or_404(User, pk=student_id, role='student')

    def has_parent_access(self, student) -> bool:
        """Check if current user has parent access to student data."""
        from apps.accounts.models import ParentAccess

        user = self.request.user

        if student is None:
            return False

        # Admin can access all
        if user.is_admin:
            return True

        # Student can access their own data
        if user.id == student.id:
            return True

        # Parent with role='parent' - check ParentAccess
        if user.is_parent:
            return ParentAccess.objects.filter(
                parent=user,
                student=student,
                is_active=True,
            ).exists()

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

    Allows access for:
    1. Users with role='parent'
    2. Admin users
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        if not (request.user.is_parent or request.user.is_admin):
            raise PermissionDenied('Wymagane uprawnienia rodzica.')

        return super().dispatch(request, *args, **kwargs)

    def get_children(self, user):
        """Get students (children) for this parent."""
        from apps.accounts.models import ParentAccess, User

        if user.is_admin:
            return User.objects.filter(role='student', is_active=True)

        # Get children via ParentAccess model
        child_ids = ParentAccess.objects.filter(
            parent=user,
            is_active=True,
        ).values_list('student_id', flat=True)

        return User.objects.filter(id__in=child_ids, is_active=True)
