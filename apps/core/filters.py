import django_filters

from .models import AuditLog


class AuditLogFilter(django_filters.FilterSet):
    """Filter for audit logs."""

    action = django_filters.ChoiceFilter(
        choices=AuditLog.ACTION_CHOICES,
        empty_label='Wszystkie akcje',
    )
    model_type = django_filters.CharFilter(
        lookup_expr='icontains',
        label='Typ modelu',
    )
    user = django_filters.CharFilter(
        field_name='user__email',
        lookup_expr='icontains',
        label='Email użytkownika',
    )
    date_from = django_filters.DateFilter(
        field_name='created_at',
        lookup_expr='gte',
        label='Data od',
    )
    date_to = django_filters.DateFilter(
        field_name='created_at',
        lookup_expr='lte',
        label='Data do',
    )

    class Meta:
        model = AuditLog
        fields = ['action', 'model_type', 'user']
