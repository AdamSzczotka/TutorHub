from django.contrib import admin

from .models import TutorProfile, TutorSubject


@admin.register(TutorProfile)
class TutorProfileAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'hourly_rate',
        'experience_years',
        'is_verified',
        'lessons_completed',
    ]
    list_filter = ['is_verified']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    raw_id_fields = ['user']


@admin.register(TutorSubject)
class TutorSubjectAdmin(admin.ModelAdmin):
    list_display = ['tutor', 'subject', 'level', 'rate_per_hour', 'is_active']
    list_filter = ['is_active', 'subject', 'level']
    raw_id_fields = ['tutor']
