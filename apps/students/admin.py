from django.contrib import admin

from .models import StudentProfile


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'class_name',
        'parent_name',
        'total_lessons',
        'completed_lessons',
    ]
    search_fields = [
        'user__email',
        'user__first_name',
        'user__last_name',
        'parent_name',
    ]
    raw_id_fields = ['user']
