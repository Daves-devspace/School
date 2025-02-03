import logging

from django.core.cache import cache
from .models import SmsProviderToken


def get_sms_provider_token():
    # Attempt to fetch the token from the cache
    token = cache.get('sms_provider_token')

    if token is None:
        # Fetch the most recent SmsProviderToken object
        token_obj = SmsProviderToken.objects.first()  # You can adjust this to get the latest record if needed
        if token_obj:
            # Return both the api_token and sender_id in the dictionary
            token = {
                "api_token": token_obj.api_token,
                "sender_id": token_obj.sender_id,
            }
            # Save the token in the cache for 1 hour
            cache.set('sms_provider_token', token, timeout=3600)
        else:
            # If no token object is found, return None
            token = None

    return token
