from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Appointment


@receiver(post_save, sender=Appointment)
def notify_appointment(sender, instance, **kwargs):
    channel_layer = get_channel_layer()

    # Fetch count once to avoid unnecessary DB queries
    count = Appointment.objects.count()

    async_to_sync(channel_layer.group_send)(
        "appointments",
        {
            "type": "send_appointment_count",
            "count": count
        }
    )

    async_to_sync(channel_layer.group_send)(
        "appointments",
        {
            "type": "new_appointment",
            "message": "New appointment received!"
        }
    )
