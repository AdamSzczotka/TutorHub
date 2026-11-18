"""Who may start a conversation with whom.

- admin:   anyone
- student: only their own tutors
- parent:  admins and the tutors of their children
- tutor:   admins, their own students and those students' parents

Replies inside an existing conversation are governed by participation,
not by these rules (e.g. a student can answer a message from an admin).
"""

from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()


def _tutor_ids_for_students(student_ids):
    from apps.accounts.models import UserRelationship
    from apps.lessons.models import LessonStudent

    via_lessons = LessonStudent.objects.filter(student_id__in=student_ids).values(
        'lesson__tutor_id'
    )
    via_relationship = UserRelationship.objects.filter(
        to_user_id__in=student_ids,
        relationship_type=UserRelationship.RelationshipType.TUTOR_STUDENT,
        is_active=True,
    ).values('from_user_id')
    return Q(id__in=via_lessons) | Q(id__in=via_relationship)


def allowed_recipients(user):
    """Queryset of active users `user` may start a conversation with."""
    from apps.accounts.models import ParentAccess, UserRelationship
    from apps.lessons.models import LessonStudent

    active = User.objects.filter(is_active=True).exclude(id=user.id)

    if user.is_admin:
        return active

    if user.is_student:
        return active.filter(role='tutor').filter(_tutor_ids_for_students([user.id]))

    if user.is_parent:
        children = ParentAccess.objects.filter(
            parent=user, is_active=True, can_message_tutors=True
        ).values_list('student_id', flat=True)
        tutors = Q(role='tutor') & _tutor_ids_for_students(list(children))
        return active.filter(Q(role='admin') | tutors)

    if user.is_tutor:
        student_ids = set(
            LessonStudent.objects.filter(lesson__tutor=user).values_list('student_id', flat=True)
        ) | set(
            UserRelationship.objects.filter(
                from_user=user,
                relationship_type=UserRelationship.RelationshipType.TUTOR_STUDENT,
                is_active=True,
            ).values_list('to_user_id', flat=True)
        )
        parent_ids = ParentAccess.objects.filter(
            student_id__in=student_ids, is_active=True
        ).values('parent_id')
        return active.filter(
            Q(role='admin') | Q(id__in=student_ids) | Q(id__in=parent_ids)
        )

    return active.none()
