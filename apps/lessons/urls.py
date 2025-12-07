from django.urls import path

from . import api_views, views

app_name = 'lessons'

urlpatterns = [
    # Calendar views
    path('calendar/', views.CalendarView.as_view(), name='calendar'),
    path(
        'calendar/resources/',
        views.ResourceCalendarView.as_view(),
        name='calendar_resources',
    ),
    # Lesson CRUD
    path('', views.LessonListView.as_view(), name='list'),
    path('create/', views.LessonCreateView.as_view(), name='create'),
    path('<int:pk>/', views.LessonDetailView.as_view(), name='detail'),
    path('<int:pk>/update/', views.LessonUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.LessonDeleteView.as_view(), name='delete'),
    # Group lesson student management
    path(
        '<int:pk>/students/',
        views.LessonStudentsView.as_view(),
        name='students',
    ),
    path(
        '<int:pk>/students/add/',
        views.AddStudentToLessonView.as_view(),
        name='add_student',
    ),
    path(
        '<int:pk>/students/<int:student_pk>/remove/',
        views.RemoveStudentFromLessonView.as_view(),
        name='remove_student',
    ),
    # iCal export
    path('export/ical/', views.ICalExportView.as_view(), name='export_ical'),
    # API endpoints
    path('api/events/', api_views.CalendarEventsAPIView.as_view(), name='api_events'),
    path(
        'api/events/<int:pk>/move/',
        api_views.EventMoveAPIView.as_view(),
        name='api_event_move',
    ),
    path(
        'api/events/<int:pk>/resize/',
        api_views.EventResizeAPIView.as_view(),
        name='api_event_resize',
    ),
    path(
        'api/resources/',
        api_views.ResourcesAPIView.as_view(),
        name='api_resources',
    ),
    path(
        'api/students/<int:pk>/check-availability/',
        views.CheckStudentAvailabilityView.as_view(),
        name='api_check_student_availability',
    ),
]
