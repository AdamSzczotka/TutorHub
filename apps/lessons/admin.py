from django.contrib import admin

from .models import Lesson, LessonStudent


class LessonStudentInline(admin.TabularInline):
    model = LessonStudent
    extra = 1
    raw_id_fields = ['student', 'attendance_marked_by']


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'subject', 'tutor', 'start_time', 'end_time', 'status']
    list_filter = ['status', 'subject', 'is_group_lesson', 'is_recurring']
    search_fields = ['title', 'tutor__email', 'tutor__first_name', 'tutor__last_name']
    raw_id_fields = ['tutor', 'parent_lesson']
    date_hierarchy = 'start_time'
    inlines = [LessonStudentInline]


@admin.register(LessonStudent)
class LessonStudentAdmin(admin.ModelAdmin):
    list_display = ['lesson', 'student', 'attendance_status', 'attendance_marked_at']
    list_filter = ['attendance_status']
    raw_id_fields = ['lesson', 'student', 'attendance_marked_by']
