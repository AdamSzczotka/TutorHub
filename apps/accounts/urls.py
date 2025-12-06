"""URL configuration for accounts app."""

from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    # User CRUD
    path('users/', views.UserListView.as_view(), name='user-list'),
    path('users/create/', views.UserCreateView.as_view(), name='user-create'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user-detail'),
    path('users/<int:pk>/edit/', views.UserUpdateView.as_view(), name='user-update'),
    path('users/<int:pk>/delete/', views.UserDeleteView.as_view(), name='user-delete'),

    # User status management
    path('users/<int:pk>/toggle-status/', views.UserStatusToggleView.as_view(), name='user-toggle-status'),

    # Password management
    path('users/<int:pk>/reset-password/', views.PasswordResetView.as_view(), name='user-reset-password'),
    path('first-login/', views.FirstLoginPasswordChangeView.as_view(), name='first-login-password'),

    # Data export (RODO)
    path('users/export/', views.UserExportView.as_view(), name='user-export'),
    path('users/<int:pk>/export-data/', views.UserDataExportView.as_view(), name='user-data-export'),

    # Bulk operations
    path('users/bulk-action/', views.UserBulkActionView.as_view(), name='user-bulk-action'),

    # Profile completion
    path('users/incomplete-profiles/', views.ProfileCompletionView.as_view(), name='profile-completion'),
    path('users/<int:pk>/mark-complete/', views.MarkProfileCompleteView.as_view(), name='mark-profile-complete'),

    # Parent contact management
    path('parent-contacts/', views.ParentContactListView.as_view(), name='parent-contact-list'),
    path('parent-contacts/<int:pk>/edit/', views.ParentContactUpdateView.as_view(), name='parent-contact-update'),

    # Analytics
    path('analytics/', views.UserAnalyticsDashboardView.as_view(), name='user-analytics'),
]
