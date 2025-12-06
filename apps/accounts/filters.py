"""Filters for accounts app."""

import django_filters
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class UserFilter(django_filters.FilterSet):
    """Filter for user list."""

    search = django_filters.CharFilter(
        method='filter_search',
        label='Szukaj',
    )
    role = django_filters.ChoiceFilter(
        choices=[
            ('admin', 'Administrator'),
            ('tutor', 'Korepetytor'),
            ('student', 'Uczeń'),
        ],
        label='Rola',
    )
    is_active = django_filters.BooleanFilter(label='Aktywny')
    is_profile_completed = django_filters.BooleanFilter(label='Profil uzupełniony')
    date_joined_from = django_filters.DateFilter(
        field_name='date_joined',
        lookup_expr='gte',
        label='Dołączył od',
    )
    date_joined_to = django_filters.DateFilter(
        field_name='date_joined',
        lookup_expr='lte',
        label='Dołączył do',
    )

    class Meta:
        model = User
        fields = ['role', 'is_active', 'is_profile_completed']

    def filter_search(self, queryset, name, value):
        """Filter by email, first name, or last name."""
        return queryset.filter(
            models.Q(email__icontains=value) |
            models.Q(first_name__icontains=value) |
            models.Q(last_name__icontains=value) |
            models.Q(phone__icontains=value)
        )
