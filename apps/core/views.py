from django.contrib.auth.mixins import LoginRequiredMixin
from django_filters.views import FilterView

from apps.core.mixins import AdminRequiredMixin, HTMXMixin

from .filters import AuditLogFilter
from .models import AuditLog


class AuditLogListView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, FilterView):
    """List and filter audit logs."""

    model = AuditLog
    template_name = 'admin_panel/audit/list.html'
    partial_template_name = 'admin_panel/audit/partials/_audit_list.html'
    context_object_name = 'logs'
    filterset_class = AuditLogFilter
    paginate_by = 50

    def get_queryset(self):
        """Return audit logs with related users."""
        return AuditLog.objects.select_related('user').order_by('-created_at')

    def get_context_data(self, **kwargs):
        """Add page title to context."""
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Logi audytu'
        return context
