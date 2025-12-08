from django.contrib import admin

from .models import AttendanceAlert, AttendanceReport


@admin.register(AttendanceAlert)
class AttendanceAlertAdmin(admin.ModelAdmin):
    list_display = [
        'student',
        'attendance_rate',
        'threshold',
        'alert_type',
        'status',
        'created_at',
    ]
    list_filter = ['status', 'alert_type', 'created_at']
    search_fields = ['student__email', 'student__first_name', 'student__last_name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(AttendanceReport)
class AttendanceReportAdmin(admin.ModelAdmin):
    list_display = [
        'student',
        'month',
        'attendance_rate',
        'total_lessons',
        'present_count',
        'absent_count',
        'late_count',
    ]
    list_filter = ['month']
    search_fields = ['student__email', 'student__first_name', 'student__last_name']
    readonly_fields = ['created_at', 'updated_at']
