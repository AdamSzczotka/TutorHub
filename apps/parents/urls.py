"""URL configuration for parents app."""

from django.urls import path

from apps.parents import views

app_name = 'parents'

urlpatterns = [
    # Dashboard
    path('', views.ParentDashboardView.as_view(), name='dashboard'),
    path('select-child/<int:student_id>/', views.ParentChildSelectView.as_view(), name='select-child'),
    # Attendance
    path('attendance/', views.ParentAttendanceView.as_view(), name='attendance'),
    # Invoices
    path('invoices/', views.ParentInvoicesView.as_view(), name='invoices'),
    # Tutors
    path('tutors/', views.ParentTutorsView.as_view(), name='tutors'),
    # Calendar
    path('calendar/', views.ParentCalendarView.as_view(), name='calendar'),
    path('calendar/events/', views.ParentCalendarEventsView.as_view(), name='calendar-events'),
    # Progress
    path('progress/', views.ParentProgressView.as_view(), name='progress'),
]
