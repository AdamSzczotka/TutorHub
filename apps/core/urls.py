from django.urls import path

from . import views

app_name = 'core'

urlpatterns = [
    path('audit/', views.AuditLogListView.as_view(), name='audit-list'),
]
