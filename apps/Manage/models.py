
from django.db import models

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

