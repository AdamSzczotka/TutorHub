from django.urls import path

from . import views

app_name = 'admin_panel'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('stats/', views.StatsView.as_view(), name='stats'),
    path('settings/', views.SettingsView.as_view(), name='settings'),
    path('activity/', views.ActivityMonitoringView.as_view(), name='activity'),
    path('health/', views.HealthMonitoringView.as_view(), name='health'),
]
