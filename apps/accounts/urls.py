"""URL configuration for accounts app."""

from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),

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

    # Profile completion tracking (admin)
    path('users/incomplete-profiles/', views.ProfileCompletionView.as_view(), name='profile-completion'),
    path('users/<int:pk>/mark-complete/', views.MarkProfileCompleteView.as_view(), name='mark-profile-complete'),

    # Profile wizard (user self-service)
    path('profile/wizard/', views.ProfileWizardView.as_view(), name='profile-wizard'),
    path('profile/step/<str:step_id>/', views.ProfileStepView.as_view(), name='profile-step'),

    # Avatar management
    path('profile/avatar/upload/', views.AvatarUploadView.as_view(), name='avatar-upload'),
    path('profile/avatar/delete/', views.AvatarDeleteView.as_view(), name='avatar-delete'),

    # User import
    path('users/import/', views.UserImportView.as_view(), name='user-import'),

    # Parent contact management
    path('parent-contacts/', views.ParentContactListView.as_view(), name='parent-contact-list'),
    path('parent-contacts/<int:pk>/edit/', views.ParentContactUpdateView.as_view(), name='parent-contact-update'),

    # Analytics
    path('analytics/', views.UserAnalyticsDashboardView.as_view(), name='user-analytics'),

    # Authentication
    path('logout/', views.LogoutView.as_view(), name='logout'),

    # ==========================================================================
    # Task 036: Notification Preferences
    # ==========================================================================
    path('settings/notifications/', views.NotificationPreferencesView.as_view(), name='notification-preferences'),

    # ==========================================================================
    # Task 038: User Relationships
    # ==========================================================================
    path('relationships/', views.UserRelationshipListView.as_view(), name='relationship-list'),
    path('relationships/create/', views.UserRelationshipCreateView.as_view(), name='relationship-create'),
    path('relationships/<int:pk>/edit/', views.UserRelationshipUpdateView.as_view(), name='relationship-update'),
    path('relationships/<int:pk>/delete/', views.UserRelationshipDeleteView.as_view(), name='relationship-delete'),
    path('my-students/', views.TutorStudentsView.as_view(), name='my-students'),

    # ==========================================================================
    # Task 039: User Activity Tracking
    # ==========================================================================
    path('activity/', views.UserActivityListView.as_view(), name='activity-list'),
    path('activity/user/<int:pk>/', views.UserActivityDetailView.as_view(), name='user-activity'),
    path('my-activity/', views.MyActivityView.as_view(), name='my-activity'),

    # ==========================================================================
    # Task 041: User Archive
    # ==========================================================================
    path('archives/', views.UserArchiveListView.as_view(), name='archive-list'),
    path('archives/<int:pk>/', views.UserArchiveDetailView.as_view(), name='archive-detail'),
    path('archives/<int:pk>/anonymize/', views.UserArchiveAnonymizeView.as_view(), name='archive-anonymize'),
    path('users/<int:pk>/archive/', views.UserArchiveCreateView.as_view(), name='user-archive'),

    # ==========================================================================
    # Task 042: User Verification
    # ==========================================================================
    path('verify/send/', views.SendVerificationView.as_view(), name='send-verification'),
    path('verify/<str:token>/', views.VerifyTokenView.as_view(), name='verify-token'),
    path('verification-status/', views.VerificationStatusView.as_view(), name='verification-status'),

    # ==========================================================================
    # Task 043: Parent Portal Access
    # ==========================================================================
    path('parent-access/', views.ParentAccessListView.as_view(), name='parent-access-list'),
    path('parent-access/invite/', views.ParentAccessCreateView.as_view(), name='parent-access-create'),
    path('parent-access/invite/<int:student_id>/', views.ParentAccessCreateView.as_view(), name='parent-access-create-for-student'),
    path('parent-access/<int:pk>/edit/', views.ParentAccessUpdateView.as_view(), name='parent-access-update'),
    path('parent-access/<int:pk>/revoke/', views.ParentAccessRevokeView.as_view(), name='parent-access-revoke'),
    path('parent-access/<int:pk>/resend/', views.ParentAccessResendInvitationView.as_view(), name='parent-access-resend'),
    path('parent-invitation/<str:token>/', views.AcceptParentInvitationView.as_view(), name='accept-parent-invitation'),
    path('my-children/', views.MyChildrenView.as_view(), name='my-children'),
    path('my-children/<int:pk>/', views.ChildDetailView.as_view(), name='child-detail'),
]
