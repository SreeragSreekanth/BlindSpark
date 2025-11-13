from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('<int:match_id>/', views.chatroom, name='chatroom'),
    path('<int:chat_id>/fetch/', views.fetch_messages, name='fetch_messages'),
    path('<int:chat_id>/send/', views.send_message, name='send_message'),
    path('', views.chat_list, name='chat_list'),
    path('message/<int:message_id>/delete/', views.delete_message, name='delete_message'),
    path('<int:match_id>/reveal/request/', views.request_reveal, name='request_reveal'),
    path('<int:match_id>/reveal/accept/', views.accept_reveal, name='accept_reveal'),


]
