"""URL configuration for student portal."""

from django.urls import path

from . import views

app_name = 'students'

urlpatterns = [
    # Dashboard
    path('', views.StudentDashboardView.as_view(), name='dashboard'),
    # Calendar
    path('calendar/', views.StudentCalendarView.as_view(), name='calendar'),
    path(
        'calendar/events/',
        views.StudentCalendarEventsView.as_view(),
        name='calendar-events',
    ),
    # Lessons
    path(
        'lessons/<int:pk>/',
        views.StudentLessonDetailView.as_view(),
        name='lesson-detail',
    ),
    # Cancellations
    path(
        'cancellations/',
        views.CancellationRequestListView.as_view(),
        name='cancellation-list',
    ),
    path(
        'cancellations/create/',
        views.CancellationRequestCreateView.as_view(),
        name='cancellation-create',
    ),
    # Makeup lessons
    path('makeup/', views.MakeupLessonsListView.as_view(), name='makeup-list'),
    # Progress
    path('progress/', views.StudentProgressView.as_view(), name='progress'),
]
