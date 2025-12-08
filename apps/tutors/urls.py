from django.urls import path

from . import views

app_name = 'tutor'

urlpatterns = [
    path('', views.TutorDashboardView.as_view(), name='dashboard'),
    path('lessons/', views.TutorLessonsView.as_view(), name='lessons'),
    path('lessons/events/', views.TutorCalendarEventsView.as_view(), name='calendar_events'),
    path('lessons/<int:lesson_id>/', views.TutorLessonDetailView.as_view(), name='lesson_detail'),
    path(
        'lessons/<int:lesson_id>/attendance/',
        views.TutorQuickAttendanceView.as_view(),
        name='quick_attendance',
    ),
    path('students/', views.TutorStudentsView.as_view(), name='students'),
    path('students/<int:student_id>/', views.TutorStudentDetailView.as_view(), name='student_detail'),
    path('attendance/', views.TutorAttendanceView.as_view(), name='attendance'),
    path('earnings/', views.TutorEarningsView.as_view(), name='earnings'),
]
