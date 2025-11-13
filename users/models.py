from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import date
from datetime import timedelta

class Interest(models.Model):
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        ordering = ['name']
    def __str__(self): return self.name


class User(AbstractUser):
    dob = models.DateField("Date of Birth", null=True, blank=True)    
    gender = models.CharField(max_length=20, choices=[
        ('M', 'Male'), ('F', 'Female')
    ], blank=True)
    bio = models.TextField(blank=True)
    interests = models.ManyToManyField(Interest, blank=True)
    city = models.CharField(max_length=100, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    profile_photo = models.ImageField(upload_to='profile_photos/', blank=True)
    is_verified = models.BooleanField(default=False)
    last_seen = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.username
    

    @property
    def age(self):
        if not self.dob:
            return None
        today = date.today()
        return today.year - self.dob.year - (
            (today.month, today.day) < (self.dob.month, self.dob.day)
        )
    
    @property
    def is_adult(self):
        return self.age is not None and self.age >= 18
    
    @property
    def is_online(self):
        if not self.last_seen:
            return False
        return timezone.now() - self.last_seen < timedelta(minutes=2)
    

     # 🔹 Profile completion percentage
    def profile_completion(self):
        fields = {
            'age': self.age,
            'gender': self.gender,
            'bio': self.bio,
            'profile_photo': self.profile_photo,
            'city': self.city,
            'interests': self.interests.exists(),
        }

        filled = sum(1 for v in fields.values() if v)
        total = len(fields)
        base_percent = (filled / total) * 100

        # Bonus for interests & verification
        if self.interests.exists():
            base_percent += 10
        # if self.is_verified:
        #     base_percent += 10

        return min(round(base_percent), 100)
