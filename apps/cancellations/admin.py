from django.contrib import admin

from .models import CancellationRequest, MakeupLesson


@admin.register(CancellationRequest)
class CancellationRequestAdmin(admin.ModelAdmin):
    list_display = [
        'lesson',
        'student',
        'status',
        'request_date',
        'reviewed_by',
        'reviewed_at',
    ]
    list_filter = ['status', 'request_date']
    search_fields = [
        'lesson__title',
        'student__first_name',
        'student__last_name',
        'student__email',
    ]
    readonly_fields = ['request_date', 'created_at', 'updated_at']
    raw_id_fields = ['lesson', 'student', 'reviewed_by']


@admin.register(MakeupLesson)
class MakeupLessonAdmin(admin.ModelAdmin):
    list_display = [
        'original_lesson',
        'student',
        'status',
        'expires_at',
        'days_remaining',
    ]
    list_filter = ['status', 'expires_at']
    search_fields = [
        'original_lesson__title',
        'student__first_name',
        'student__last_name',
    ]
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['student', 'original_lesson', 'new_lesson']
