"""Django admin configuration for landing app."""

from django.contrib import admin

from .models import FAQItem, Lead, PageContent, SchoolInfo, TeamMember, Testimonial


@admin.register(PageContent)
class PageContentAdmin(admin.ModelAdmin):
    """Admin for page content sections."""

    list_display = ['page_key', 'title', 'is_active', 'updated_at']
    list_filter = ['is_active']
    search_fields = ['page_key', 'title', 'content']
    ordering = ['page_key']


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    """Admin for team members."""

    list_display = ['name', 'surname', 'position', 'order_index', 'is_published']
    list_filter = ['is_published']
    search_fields = ['name', 'surname', 'position']
    ordering = ['order_index']
    list_editable = ['order_index', 'is_published']


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    """Admin for testimonials."""

    list_display = [
        'student_name',
        'subject',
        'rating',
        'is_verified',
        'is_published',
        'created_at',
    ]
    list_filter = ['is_verified', 'is_published', 'rating', 'subject']
    search_fields = ['student_name', 'parent_name', 'content']
    ordering = ['display_order', '-created_at']
    list_editable = ['is_verified', 'is_published']


@admin.register(FAQItem)
class FAQItemAdmin(admin.ModelAdmin):
    """Admin for FAQ items."""

    list_display = ['question', 'category', 'order_index', 'is_published']
    list_filter = ['is_published', 'category']
    search_fields = ['question', 'answer']
    ordering = ['order_index']
    list_editable = ['order_index', 'is_published']


@admin.register(SchoolInfo)
class SchoolInfoAdmin(admin.ModelAdmin):
    """Admin for school settings."""

    list_display = ['name', 'email', 'phone', 'city']
    fieldsets = (
        ('Podstawowe', {
            'fields': ('name', 'tagline', 'description'),
        }),
        ('Kontakt', {
            'fields': ('email', 'phone'),
        }),
        ('Adres', {
            'fields': ('address', 'city', 'postal_code'),
        }),
        ('Lokalizacja', {
            'fields': ('latitude', 'longitude'),
        }),
        ('Dodatkowe', {
            'fields': ('opening_hours', 'social_media'),
            'classes': ('collapse',),
        }),
    )


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    """Admin for contact form leads."""

    list_display = ['name', 'email', 'subject', 'status', 'created_at']
    list_filter = ['status', 'gdpr_consent', 'marketing_consent', 'created_at']
    search_fields = ['name', 'email', 'subject', 'message']
    ordering = ['-created_at']
    list_editable = ['status']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
