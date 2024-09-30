from django.conf import settings
from django.db import models

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    total_reading_7days = models.IntegerField(default=0)
    total_reading_30days = models.IntegerField(default=0)
