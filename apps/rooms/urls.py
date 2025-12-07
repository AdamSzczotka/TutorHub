from django.urls import path

from . import views

app_name = 'rooms'

urlpatterns = [
    path('', views.RoomListView.as_view(), name='list'),
    path('create/', views.RoomCreateView.as_view(), name='create'),
    path('<int:pk>/edit/', views.RoomUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.RoomDeleteView.as_view(), name='delete'),
]
