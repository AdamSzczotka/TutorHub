from django.urls import path

from . import views

app_name = 'messages'

urlpatterns = [
    path('', views.ConversationListView.as_view(), name='list'),
    path('create/', views.CreateConversationView.as_view(), name='create'),
    path('search/', views.SearchMessagesView.as_view(), name='search'),
    path('unread-count/', views.UnreadCountView.as_view(), name='unread_count'),
    path('mark-read/', views.MarkAsReadView.as_view(), name='mark_read'),
    path('<uuid:pk>/', views.ConversationDetailView.as_view(), name='detail'),
    path(
        '<uuid:conversation_id>/send/',
        views.SendMessageView.as_view(),
        name='send',
    ),
    path(
        '<uuid:conversation_id>/archive/',
        views.ArchiveConversationView.as_view(),
        name='archive',
    ),
    path(
        '<uuid:conversation_id>/unarchive/',
        views.UnarchiveConversationView.as_view(),
        name='unarchive',
    ),
    path(
        '<uuid:conversation_id>/mute/',
        views.MuteConversationView.as_view(),
        name='mute',
    ),
    path(
        'message/<uuid:message_id>/edit/',
        views.EditMessageView.as_view(),
        name='edit',
    ),
    path(
        'message/<uuid:message_id>/delete/',
        views.DeleteMessageView.as_view(),
        name='delete',
    ),
]
