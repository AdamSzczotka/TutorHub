from django.apps import AppConfig


class AdminPanelConfig(AppConfig):
    """Configuration for admin_panel app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.admin_panel'
    verbose_name = 'Panel Administracyjny'
