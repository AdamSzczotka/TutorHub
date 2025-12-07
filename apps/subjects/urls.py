from django.urls import path

from . import views

app_name = 'subjects'

urlpatterns = [
    # Subjects
    path('', views.SubjectListView.as_view(), name='list'),
    path('create/', views.SubjectCreateView.as_view(), name='create'),
    path('<int:pk>/edit/', views.SubjectUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.SubjectDeleteView.as_view(), name='delete'),
    # Levels
    path('levels/', views.LevelListView.as_view(), name='level-list'),
    path('levels/create/', views.LevelCreateView.as_view(), name='level-create'),
    path('levels/<int:pk>/edit/', views.LevelUpdateView.as_view(), name='level-update'),
    path('levels/<int:pk>/delete/', views.LevelDeleteView.as_view(), name='level-delete'),
]
