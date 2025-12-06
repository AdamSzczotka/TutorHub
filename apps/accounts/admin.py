from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User admin."""

    list_display = [
        'email',
        'first_name',
        'last_name',
        'role',
        'is_active',
        'date_joined',
    ]
    list_filter = ['role', 'is_active', 'is_staff', 'is_profile_completed']
    search_fields = ['email', 'first_name', 'last_name', 'phone']
    ordering = ['-date_joined']

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Dane osobowe', {'fields': ('first_name', 'last_name', 'phone', 'avatar')}),
        ('Rola', {'fields': ('role', 'is_profile_completed', 'first_login')}),
        (
            'Uprawnienia',
            {
                'fields': (
                    'is_active',
                    'is_staff',
                    'is_superuser',
                    'groups',
                    'user_permissions',
                )
            },
        ),
        ('Daty', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': (
                    'email',
                    'first_name',
                    'last_name',
                    'role',
                    'password1',
                    'password2',
                ),
            },
        ),
    )
