from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from user.models import Profile
from user.utils import send_activation_email


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(created, **kwargs):
    """
    Signal receiver that creates a user profile when a new user is created.
    """
    instance = kwargs["instance"]
    if created and not hasattr(instance, "profile"):
        Profile.objects.create(user=instance)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def send_activation_email_(sender, instance, created, **kwargs):
    """
    Signal receiver that sends an activation email when a new user is created.
    """
    if created:
        send_activation_email(instance)
