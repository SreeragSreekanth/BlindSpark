from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('profile/', views.profile_view, name='profile'),
    path('edit/', views.edit_profile, name='edit'),

    # Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('update-last-seen/', views.update_last_seen, name='update_last_seen'),
]
