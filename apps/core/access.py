"""Object-level access helpers shared across apps.

Role mixins only answer "is this user a tutor/admin/...". These helpers answer
"may this user see data about *this* student / lesson".
"""

from django.core.exceptions import PermissionDenied


def _parent_student_ids(user, permission: str | None = None):
    from apps.accounts.models import ParentAccess

    qs = ParentAccess.objects.filter(parent=user, is_active=True)
    if permission:
        qs = qs.filter(**{permission: True})
    return qs.values('student_id')


def can_view_student(user, student_id, parent_permission: str | None = None) -> bool:
    """Admin: any student. Student: self. Parent: linked child. Tutor: own students."""
    if not user.is_authenticated:
        return False
    if user.is_admin:
        return True
    if str(user.pk) == str(student_id):
        return True
    if user.is_parent:
        return _parent_student_ids(user, parent_permission).filter(student_id=student_id).exists()
    if user.is_tutor:
        from apps.lessons.models import LessonStudent

        return LessonStudent.objects.filter(lesson__tutor=user, student_id=student_id).exists()
    return False


def require_student_access(user, student_id, parent_permission: str | None = None) -> None:
    if not can_view_student(user, student_id, parent_permission):
        raise PermissionDenied('Brak dostępu do danych tego ucznia.')


def visible_invoices(user, queryset):
    """Restrict an Invoice queryset to what the user may see."""
    if user.is_admin:
        return queryset
    if user.is_student:
        return queryset.filter(student=user)
    if user.is_parent:
        return queryset.filter(student_id__in=_parent_student_ids(user, 'can_view_invoices'))
    return queryset.none()


def lesson_for_tutor(user, lesson_id):
    """Fetch a lesson the user may manage (admin: any, tutor: own)."""
    from django.shortcuts import get_object_or_404

    from apps.lessons.models import Lesson

    if user.is_admin:
        return get_object_or_404(Lesson, pk=lesson_id)
    return get_object_or_404(Lesson, pk=lesson_id, tutor=user)
