import sys
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import connection
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils import timezone
from django.views.generic import ListView, TemplateView

from apps.accounts.models import User, UserActivity
from apps.core.mixins import AdminRequiredMixin, HTMXMixin
from apps.core.models import SystemSetting
from apps.lessons.models import Lesson


class DashboardView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    """Admin dashboard view with statistics and recent activity."""

    template_name = 'admin_panel/dashboard.html'

    def get_context_data(self, **kwargs):
        """Add dashboard statistics to context."""
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        week_ago = now - timedelta(days=7)

        # Quick stats
        context['stats'] = {
            'total_users': User.objects.filter(is_active=True).count(),
            'total_tutors': User.objects.filter(role='tutor', is_active=True).count(),
            'total_students': User.objects.filter(role='student', is_active=True).count(),
            'lessons_this_week': Lesson.objects.filter(
                start_time__gte=week_ago,
                status__in=['scheduled', 'completed']
            ).count(),
            'pending_invoices': 0,
            'monthly_revenue': 0,
        }

        # Recent activity
        context['recent_users'] = User.objects.order_by('-date_joined')[:5]
        context['upcoming_lessons'] = Lesson.objects.filter(
            start_time__gte=now,
            status='scheduled'
        ).select_related('tutor', 'subject', 'room').order_by('start_time')[:5]

        return context


class StatsView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, TemplateView):
    """HTMX endpoint for refreshing statistics cards."""

    template_name = 'admin_panel/partials/_stats_cards.html'
    partial_template_name = 'admin_panel/partials/_stats_cards.html'

    def get_context_data(self, **kwargs):
        """Add statistics to context."""
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        context['stats'] = {
            'total_users': User.objects.filter(is_active=True).count(),
            'total_tutors': User.objects.filter(role='tutor', is_active=True).count(),
            'total_students': User.objects.filter(role='student', is_active=True).count(),
            'lessons_this_week': Lesson.objects.filter(
                start_time__gte=week_ago,
                status__in=['scheduled', 'completed']
            ).count(),
            'pending_invoices': 0,
            'monthly_revenue': 0,
        }

        return context


class SettingsView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    """System settings panel view."""

    template_name = 'admin_panel/settings.html'

    def get_context_data(self, **kwargs):
        """Add settings context."""
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Ustawienia Systemu'

        # Load all settings
        context['settings'] = {
            'school_name': SystemSetting.get('school_name', 'Na Piatke'),
            'default_lesson_duration': SystemSetting.get('default_lesson_duration', 60),
            'cancellation_notice_hours': SystemSetting.get('cancellation_notice_hours', 24),
            'makeup_lesson_expiry_days': SystemSetting.get('makeup_lesson_expiry_days', 30),
            'invoice_prefix': SystemSetting.get('invoice_prefix', 'FV'),
            'notification_email': SystemSetting.get('notification_email', ''),
        }

        return context

    def post(self, request):
        """Update settings from POST data."""
        for key in request.POST:
            if key.startswith('setting_'):
                setting_key = key.replace('setting_', '')
                value = request.POST[key]

                # Try to convert to appropriate type
                try:
                    value = int(value)
                except ValueError:
                    pass  # Keep value as string if conversion fails

                SystemSetting.set(setting_key, value)

        messages.success(request, 'Ustawienia zostaly zapisane.')

        if request.htmx:
            return HttpResponse(
                status=204,
                headers={'HX-Trigger': 'settingsSaved'}
            )

        return redirect('admin_panel:settings')


class ActivityMonitoringView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, ListView):
    """Admin activity monitoring view - shows recent user activities."""

    template_name = 'admin_panel/activity_monitoring.html'
    partial_template_name = 'admin_panel/partials/_activity_table.html'
    context_object_name = 'activities'
    paginate_by = 50

    def get_queryset(self):
        """Get recent user activities with filters."""
        queryset = UserActivity.objects.select_related('user').order_by('-created_at')

        # Filter by activity type
        activity_type = self.request.GET.get('type')
        if activity_type:
            queryset = queryset.filter(activity_type=activity_type)

        # Filter by user
        user_id = self.request.GET.get('user')
        if user_id:
            queryset = queryset.filter(user_id=user_id)

        # Filter by date range
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)

        return queryset

    def get_context_data(self, **kwargs):
        """Add activity statistics to context."""
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Monitoring Aktywnosci'

        now = timezone.now()
        today = now.date()
        week_ago = now - timedelta(days=7)

        # Activity statistics
        context['activity_stats'] = {
            'today_logins': UserActivity.objects.filter(
                activity_type='login',
                created_at__date=today
            ).count(),
            'weekly_activities': UserActivity.objects.filter(
                created_at__gte=week_ago
            ).count(),
            'active_users_today': UserActivity.objects.filter(
                created_at__date=today
            ).values('user').distinct().count(),
        }

        # Activity type choices for filter
        context['activity_types'] = UserActivity.ActivityType.choices

        return context


class HealthMonitoringView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    """System health monitoring view."""

    template_name = 'admin_panel/health_monitoring.html'

    def get_context_data(self, **kwargs):
        """Add system health information to context."""
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Stan Systemu'

        # Database health
        db_status = self._check_database()

        # Cache/Redis health
        cache_status = self._check_cache()

        # System info
        context['health'] = {
            'database': db_status,
            'cache': cache_status,
            'python_version': sys.version,
            'django_version': self._get_django_version(),
            'debug_mode': settings.DEBUG,
        }

        # Database statistics
        context['db_stats'] = {
            'total_users': User.objects.count(),
            'active_users': User.objects.filter(is_active=True).count(),
            'total_lessons': Lesson.objects.count(),
        }

        # Recent errors (placeholder - would integrate with logging)
        context['recent_errors'] = []

        return context

    def _check_database(self) -> dict:
        """Check database connection health."""
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
            return {'status': 'healthy', 'message': 'Polaczenie aktywne'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def _check_cache(self) -> dict:
        """Check cache/Redis connection health."""
        try:
            from django.core.cache import cache
            cache.set('health_check', 'ok', 10)
            if cache.get('health_check') == 'ok':
                return {'status': 'healthy', 'message': 'Cache dziala poprawnie'}
            return {'status': 'warning', 'message': 'Cache nie odpowiada'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def _get_django_version(self) -> str:
        """Get Django version."""
        import django
        return django.get_version()
