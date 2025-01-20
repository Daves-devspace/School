from channels.generic.websocket import AsyncJsonWebsocketConsumer
from .models import Timetable

class TimetableConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive_json(self, content):
        selected_grade_section = content.get('grade_section')
        if not selected_grade_section:
            await self.send_json({"error": "Grade section not provided"})
            return

        timetable_data = await self.fetch_timetable_data(selected_grade_section)
        await self.send_json({"data": timetable_data})

    async def fetch_timetable_data(self, selected_grade_section):
        entries = Timetable.objects.filter(grade_section_id=selected_grade_section).select_related('subject', 'teacher')
        days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        timetable_data = {day: [] for day in days_of_week}

        for entry in entries:
            timetable_data[entry.day].append({
                "time": f"{entry.start_time.strftime('%I:%M %p')} - {entry.end_time.strftime('%I:%M %p')}",
                "subject": entry.subject.name,
                "teacher": entry.teacher.full_name,
            })

        return timetable_data


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = f"user_{self.scope['user'].id}"

        # Add the user to a group based on their ID
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        await self.send(text_data=json.dumps({
            'message': data['message']
        }))

    async def send_notification(self, event):
        await self.send(text_data=json.dumps(event['message']))