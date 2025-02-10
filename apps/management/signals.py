from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Profile

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    """
    Create a Profile for the new user when a User is created.
    """
    if created:
        Profile.objects.create(user=instance)  # Profile is automatically created with default role
