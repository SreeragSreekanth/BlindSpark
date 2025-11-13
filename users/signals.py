# users/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import user_logged_in
from django.utils import timezone


@receiver(user_logged_in)
def update_last_seen(sender, user, request, **kwargs):
    user.last_seen = timezone.now()
    user.save(update_fields=['last_seen'])