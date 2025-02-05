from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.Manage.validators import custom_username_validator


# # Create your models here.
class SmsProviderToken(models.Model):
    api_token = models.CharField(max_length=255)
    sender_id = models.CharField(max_length=255)

    def __str__(self):
        return f"Token: {self.sender_id}"

    def save(self, *args, **kwargs):
        """Override the save method to clear the cache when the token is updated."""
        super().save(*args, **kwargs)
        from django.core.cache import cache
        # Clear the cache so the new token can be fetched
        cache.delete('sms_provider_token')



#
# class CustomUser(AbstractUser):
#     username = models.CharField(
#         max_length=150,
#         unique=True,
#         validators=[custom_username_validator],  # Apply the custom validator here
#     )
