import json

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.db.models import Count
from .models import Appointment

class AppointmentCountConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = "appointments"

        # Join the WebSocket group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

        # Send the initial count of appointments
        count = await self.get_appointment_count()
        await self.send(text_data=json.dumps({"count": count}))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        if data.get("action") == "refresh":
            count = await self.get_appointment_count()
            await self.send(text_data=json.dumps({"count": count}))

    async def send_appointment_count(self, event):
        count = event["count"]
        await self.send(text_data=json.dumps({"count": count}))

    async def get_appointment_count(self):
        return await sync_to_async(Appointment.objects.count)()



class InboxConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("inbox_updates", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("inbox_updates", self.channel_name)

    async def new_appointment(self, event):
        await self.send(text_data=json.dumps(event))
