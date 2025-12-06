"""Permission system for napiatke project."""

from enum import Enum


class Permission(str, Enum):
    """Permission enumeration."""

    # User management
    USER_CREATE = 'user:create'
    USER_READ = 'user:read'
    USER_UPDATE = 'user:update'
    USER_DELETE = 'user:delete'
    USER_EXPORT = 'user:export'

    # Lesson management
    LESSON_CREATE = 'lesson:create'
    LESSON_READ = 'lesson:read'
    LESSON_UPDATE = 'lesson:update'
    LESSON_DELETE = 'lesson:delete'

    # Administrative
    ADMIN_DASHBOARD = 'admin:dashboard'
    ADMIN_SETTINGS = 'admin:settings'
    ADMIN_AUDIT = 'admin:audit'

    # Billing
    INVOICE_CREATE = 'invoice:create'
    INVOICE_READ = 'invoice:read'
    INVOICE_SEND = 'invoice:send'

    # Room management
    ROOM_CREATE = 'room:create'
    ROOM_READ = 'room:read'
    ROOM_UPDATE = 'room:update'
    ROOM_DELETE = 'room:delete'

    # Subject management
    SUBJECT_CREATE = 'subject:create'
    SUBJECT_READ = 'subject:read'
    SUBJECT_UPDATE = 'subject:update'
    SUBJECT_DELETE = 'subject:delete'


ROLE_PERMISSIONS: dict[str, list[Permission]] = {
    'admin': [
        # User management
        Permission.USER_CREATE,
        Permission.USER_READ,
        Permission.USER_UPDATE,
        Permission.USER_DELETE,
        Permission.USER_EXPORT,
        # Lesson management
        Permission.LESSON_CREATE,
        Permission.LESSON_READ,
        Permission.LESSON_UPDATE,
        Permission.LESSON_DELETE,
        # Administrative
        Permission.ADMIN_DASHBOARD,
        Permission.ADMIN_SETTINGS,
        Permission.ADMIN_AUDIT,
        # Billing
        Permission.INVOICE_CREATE,
        Permission.INVOICE_READ,
        Permission.INVOICE_SEND,
        # Room management
        Permission.ROOM_CREATE,
        Permission.ROOM_READ,
        Permission.ROOM_UPDATE,
        Permission.ROOM_DELETE,
        # Subject management
        Permission.SUBJECT_CREATE,
        Permission.SUBJECT_READ,
        Permission.SUBJECT_UPDATE,
        Permission.SUBJECT_DELETE,
    ],
    'tutor': [
        Permission.USER_READ,  # Own students only
        Permission.LESSON_READ,
        Permission.LESSON_UPDATE,  # Own lessons only
        Permission.ROOM_READ,
        Permission.SUBJECT_READ,
    ],
    'student': [
        Permission.LESSON_READ,  # Own lessons only
        Permission.ROOM_READ,
        Permission.SUBJECT_READ,
    ],
}


def has_permission(user, permission: Permission) -> bool:
    """Check if user has a specific permission.

    Args:
        user: User object to check.
        permission: Permission to check for.

    Returns:
        True if user has the permission, False otherwise.
    """
    if not user.is_authenticated:
        return False

    user_permissions = ROLE_PERMISSIONS.get(user.role, [])
    return permission in user_permissions


def has_any_permission(user, permissions: list[Permission]) -> bool:
    """Check if user has any of the specified permissions.

    Args:
        user: User object to check.
        permissions: List of permissions to check for.

    Returns:
        True if user has any of the permissions, False otherwise.
    """
    return any(has_permission(user, p) for p in permissions)


def has_all_permissions(user, permissions: list[Permission]) -> bool:
    """Check if user has all specified permissions.

    Args:
        user: User object to check.
        permissions: List of permissions to check for.

    Returns:
        True if user has all permissions, False otherwise.
    """
    return all(has_permission(user, p) for p in permissions)


def get_user_permissions(user) -> list[Permission]:
    """Get all permissions for a user.

    Args:
        user: User object.

    Returns:
        List of permissions the user has.
    """
    if not user.is_authenticated:
        return []

    return ROLE_PERMISSIONS.get(user.role, [])
