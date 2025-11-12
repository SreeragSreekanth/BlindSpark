# matches/urls.py
from django.urls import path
from . import views

app_name = 'matches'

urlpatterns = [
    path('discover/', views.discover_matches, name='discover'),
    path('view/<int:user_id>/', views.view_profile, name='view_profile'),
    path('like/<int:user_id>/', views.like_user, name='like_user'),
]