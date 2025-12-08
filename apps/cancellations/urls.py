from django.urls import path

from . import views

app_name = 'cancellations'

urlpatterns = [
    # Student views - Cancellations
    path(
        'request/<int:lesson_id>/',
        views.CancellationRequestFormView.as_view(),
        name='request_form',
    ),
    path(
        'request/<int:lesson_id>/create/',
        views.CreateCancellationRequestView.as_view(),
        name='create',
    ),
    path(
        'my-requests/',
        views.StudentCancellationsView.as_view(),
        name='my_requests',
    ),
    # Student views - Makeup lessons
    path(
        'makeup/',
        views.MakeupLessonsListView.as_view(),
        name='makeup_list',
    ),
    path(
        'makeup/<int:makeup_id>/reschedule/',
        views.RescheduleFormView.as_view(),
        name='reschedule_form',
    ),
    path(
        'makeup/<int:makeup_id>/schedule/',
        views.ScheduleMakeupView.as_view(),
        name='schedule_makeup',
    ),
    # Admin views - Cancellations
    path(
        'admin/queue/',
        views.AdminCancellationQueueView.as_view(),
        name='admin_queue',
    ),
    path(
        'admin/review/<int:request_id>/',
        views.ReviewCancellationView.as_view(),
        name='review',
    ),
    path(
        'admin/review/<int:request_id>/form/',
        views.ReviewFormView.as_view(),
        name='review_form',
    ),
    # Admin views - Makeup lessons
    path(
        'admin/makeup/',
        views.AdminMakeupListView.as_view(),
        name='admin_makeup_list',
    ),
    path(
        'admin/makeup/<int:makeup_id>/extend/',
        views.ExtendDeadlineView.as_view(),
        name='extend_deadline',
    ),
    path(
        'admin/makeup/<int:makeup_id>/extend/form/',
        views.ExtendDeadlineFormView.as_view(),
        name='extend_deadline_form',
    ),
    path(
        'admin/makeup/statistics/',
        views.MakeupStatisticsView.as_view(),
        name='makeup_statistics',
    ),
]
