from django.urls import path

from . import views

app_name = 'attendance'

urlpatterns = [
    # Overview
    path(
        '',
        views.AttendanceOverviewView.as_view(),
        name='overview',
    ),
    # Attendance marking
    path(
        'lesson/<int:lesson_id>/',
        views.AttendanceMarkingView.as_view(),
        name='marking',
    ),
    path(
        'lesson/<int:lesson_id>/mark/',
        views.MarkAttendanceAPIView.as_view(),
        name='mark',
    ),
    path(
        'lesson/<int:lesson_id>/bulk/',
        views.BulkMarkAttendanceView.as_view(),
        name='bulk_mark',
    ),
    # Time tracking
    path(
        'lesson/<int:lesson_id>/student/<int:student_id>/check-in/',
        views.CheckInView.as_view(),
        name='check_in',
    ),
    path(
        'lesson/<int:lesson_id>/student/<int:student_id>/check-out/',
        views.CheckOutView.as_view(),
        name='check_out',
    ),
    # History
    path(
        'student/<int:student_id>/history/',
        views.AttendanceHistoryView.as_view(),
        name='history',
    ),
    # Statistics
    path(
        'statistics/',
        views.StudentStatisticsView.as_view(),
        name='statistics',
    ),
    path(
        'statistics/<int:student_id>/',
        views.StudentStatisticsView.as_view(),
        name='student_statistics',
    ),
    path(
        'statistics/<int:student_id>/chart/',
        views.AttendanceChartDataView.as_view(),
        name='chart_data',
    ),
    path(
        'low-attendance/',
        views.LowAttendanceListView.as_view(),
        name='low_attendance',
    ),
    # Alerts
    path(
        'alerts/',
        views.AttendanceAlertListView.as_view(),
        name='alerts',
    ),
    path(
        'alerts/check/',
        views.CheckAlertsView.as_view(),
        name='check_alerts',
    ),
    path(
        'alerts/<int:alert_id>/resolve/',
        views.ResolveAlertView.as_view(),
        name='resolve_alert',
    ),
    path(
        'alerts/<int:alert_id>/resolve/form/',
        views.ResolveAlertFormView.as_view(),
        name='resolve_alert_form',
    ),
    path(
        'alerts/<int:alert_id>/dismiss/',
        views.DismissAlertView.as_view(),
        name='dismiss_alert',
    ),
    # Reports
    path(
        'reports/<int:student_id>/generate/',
        views.GenerateReportView.as_view(),
        name='generate_report',
    ),
    path(
        'reports/bulk-generate/',
        views.BulkGenerateReportsView.as_view(),
        name='bulk_generate_reports',
    ),
    # Export
    path(
        'export/',
        views.ExportPageView.as_view(),
        name='export',
    ),
    path(
        'export/csv/',
        views.ExportCSVView.as_view(),
        name='export_csv',
    ),
    path(
        'export/modal/',
        views.ExportModalView.as_view(),
        name='export_modal',
    ),
]
