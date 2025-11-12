# matches/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone

User = settings.AUTH_USER_MODEL

class Match(models.Model):
    user_a = models.ForeignKey(User, on_delete=models.CASCADE, related_name='matches_a')
    user_b = models.ForeignKey(User, on_delete=models.CASCADE, related_name='matches_b')
    compatibility_score = models.FloatField(default=0.0)
    matched_on = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('user_a', 'user_b')
        ordering = ['-compatibility_score', '-matched_on']

    def __str__(self):
        return f"{self.user_a} ↔ {self.user_b} ({self.compatibility_score:.1f}%)"


class DiscoveryLog(models.Model):
    viewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='discovery_logs')
    viewed_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='been_viewed_logs')
    viewed_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-viewed_on']
        unique_together = ('viewer', 'viewed_user')

    def __str__(self):
        return f"{self.viewer} → {self.viewed_user}"


class Like(models.Model):
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes_sent')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes_received')
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('from_user', 'to_user')
        ordering = ['-created_on']

    def __str__(self):
        return f"{self.from_user} → {self.to_user}"

    @property
    def is_mutual(self):
        return Like.objects.filter(from_user=self.to_user, to_user=self.from_user).exists()