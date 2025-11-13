from django.db import models
from django.conf import settings


User = settings.AUTH_USER_MODEL


# Create your models here.
class ChatRoom(models.Model):
    match = models.OneToOneField('match.Match', on_delete=models.CASCADE, related_name='chatroom')
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ChatRoom for {self.match}"


class Message(models.Model):
    chat = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.sender} → {self.text[:25]}"
