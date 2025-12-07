"""URL configuration for landing app."""

from django.urls import path

from . import views

app_name = 'landing'

urlpatterns = [
    # Public pages
    path('', views.LandingPageView.as_view(), name='home'),
    path('kontakt/', views.ContactFormView.as_view(), name='contact'),
    path('polityka-prywatnosci/', views.PrivacyPolicyView.as_view(), name='privacy_policy'),

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

    # Statistics Management
    path('cms/statistics/', views.StatisticListView.as_view(), name='cms-statistic-list'),
    path('cms/statistics/create/', views.StatisticCreateView.as_view(), name='cms-statistic-create'),
    path('cms/statistics/<int:pk>/edit/', views.StatisticUpdateView.as_view(), name='cms-statistic-update'),
    path('cms/statistics/<int:pk>/delete/', views.StatisticDeleteView.as_view(), name='cms-statistic-delete'),

    # Why Us Cards Management
    path('cms/whyus/', views.WhyUsCardListView.as_view(), name='cms-whyus-list'),
    path('cms/whyus/create/', views.WhyUsCardCreateView.as_view(), name='cms-whyus-create'),
    path('cms/whyus/<int:pk>/edit/', views.WhyUsCardUpdateView.as_view(), name='cms-whyus-update'),
    path('cms/whyus/<int:pk>/delete/', views.WhyUsCardDeleteView.as_view(), name='cms-whyus-delete'),
    path('cms/whyus/reorder/', views.WhyUsCardReorderView.as_view(), name='cms-whyus-reorder'),

    # Subjects Management
    path('cms/subjects/', views.SubjectListView.as_view(), name='cms-subject-list'),
    path('cms/subjects/create/', views.SubjectCreateView.as_view(), name='cms-subject-create'),
    path('cms/subjects/<int:pk>/edit/', views.SubjectUpdateView.as_view(), name='cms-subject-update'),
    path('cms/subjects/<int:pk>/delete/', views.SubjectDeleteView.as_view(), name='cms-subject-delete'),
    path('cms/subjects/reorder/', views.SubjectReorderView.as_view(), name='cms-subject-reorder'),

    # Pricing Packages Management
    path('cms/pricing/', views.PricingPackageListView.as_view(), name='cms-pricing-list'),
    path('cms/pricing/create/', views.PricingPackageCreateView.as_view(), name='cms-pricing-create'),
    path('cms/pricing/<int:pk>/edit/', views.PricingPackageUpdateView.as_view(), name='cms-pricing-update'),
    path('cms/pricing/<int:pk>/delete/', views.PricingPackageDeleteView.as_view(), name='cms-pricing-delete'),
    path('cms/pricing/reorder/', views.PricingPackageReorderView.as_view(), name='cms-pricing-reorder'),

    # Education Levels Management
    path('cms/levels/', views.EducationLevelListView.as_view(), name='cms-level-list'),
    path('cms/levels/create/', views.EducationLevelCreateView.as_view(), name='cms-level-create'),
    path('cms/levels/<int:pk>/edit/', views.EducationLevelUpdateView.as_view(), name='cms-level-update'),
    path('cms/levels/<int:pk>/delete/', views.EducationLevelDeleteView.as_view(), name='cms-level-delete'),

    # Lesson Types Management
    path('cms/lessontypes/', views.LessonTypeListView.as_view(), name='cms-lessontype-list'),
    path('cms/lessontypes/create/', views.LessonTypeCreateView.as_view(), name='cms-lessontype-create'),
    path('cms/lessontypes/<int:pk>/edit/', views.LessonTypeUpdateView.as_view(), name='cms-lessontype-update'),
    path('cms/lessontypes/<int:pk>/delete/', views.LessonTypeDeleteView.as_view(), name='cms-lessontype-delete'),
]
