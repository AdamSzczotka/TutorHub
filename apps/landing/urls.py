"""URL configuration for landing app."""

from django.urls import path

from . import views

app_name = 'landing'

urlpatterns = [
    # Public pages
    path('', views.LandingPageView.as_view(), name='home'),
    path('kontakt/', views.ContactFormView.as_view(), name='contact'),

    # ==========================================================================
    # CMS Admin Panel
    # ==========================================================================
    path('cms/', views.CMSDashboardView.as_view(), name='cms-dashboard'),

    # Page Content Management
    path('cms/content/', views.PageContentListView.as_view(), name='cms-content-list'),
    path('cms/content/create/', views.PageContentCreateView.as_view(), name='cms-content-create'),
    path('cms/content/<int:pk>/edit/', views.PageContentUpdateView.as_view(), name='cms-content-update'),
    path('cms/content/<int:pk>/delete/', views.PageContentDeleteView.as_view(), name='cms-content-delete'),
    path('cms/content/<int:pk>/toggle/', views.PageContentToggleView.as_view(), name='cms-content-toggle'),

    # Team Members Management
    path('cms/team/', views.TeamMemberListView.as_view(), name='cms-team-list'),
    path('cms/team/create/', views.TeamMemberCreateView.as_view(), name='cms-team-create'),
    path('cms/team/<int:pk>/edit/', views.TeamMemberUpdateView.as_view(), name='cms-team-update'),
    path('cms/team/<int:pk>/delete/', views.TeamMemberDeleteView.as_view(), name='cms-team-delete'),
    path('cms/team/<int:pk>/toggle/', views.TeamMemberToggleView.as_view(), name='cms-team-toggle'),
    path('cms/team/reorder/', views.TeamMemberReorderView.as_view(), name='cms-team-reorder'),

    # Testimonials Management
    path('cms/testimonials/', views.TestimonialListView.as_view(), name='cms-testimonial-list'),
    path('cms/testimonials/create/', views.TestimonialCreateView.as_view(), name='cms-testimonial-create'),
    path('cms/testimonials/<int:pk>/edit/', views.TestimonialUpdateView.as_view(), name='cms-testimonial-update'),
    path('cms/testimonials/<int:pk>/delete/', views.TestimonialDeleteView.as_view(), name='cms-testimonial-delete'),
    path('cms/testimonials/<int:pk>/approve/', views.TestimonialApproveView.as_view(), name='cms-testimonial-approve'),
    path('cms/testimonials/<int:pk>/toggle/', views.TestimonialToggleView.as_view(), name='cms-testimonial-toggle'),

    # FAQ Management
    path('cms/faq/', views.FAQListView.as_view(), name='cms-faq-list'),
    path('cms/faq/create/', views.FAQCreateView.as_view(), name='cms-faq-create'),
    path('cms/faq/<int:pk>/edit/', views.FAQUpdateView.as_view(), name='cms-faq-update'),
    path('cms/faq/<int:pk>/delete/', views.FAQDeleteView.as_view(), name='cms-faq-delete'),
    path('cms/faq/<int:pk>/toggle/', views.FAQToggleView.as_view(), name='cms-faq-toggle'),
    path('cms/faq/reorder/', views.FAQReorderView.as_view(), name='cms-faq-reorder'),

    # School Settings
    path('cms/settings/', views.SchoolSettingsView.as_view(), name='cms-school-settings'),

    # Leads Management
    path('cms/leads/', views.LeadListView.as_view(), name='cms-lead-list'),
    path('cms/leads/<int:pk>/', views.LeadDetailView.as_view(), name='cms-lead-detail'),
    path('cms/leads/<int:pk>/status/', views.LeadStatusUpdateView.as_view(), name='cms-lead-status'),
    path('cms/leads/<int:pk>/delete/', views.LeadDeleteView.as_view(), name='cms-lead-delete'),
]
