from django.urls import path
from .consumers import TimetableConsumer, NotificationConsumer

websocket_urlpatterns = [
    path('ws/timetable/', TimetableConsumer.as_asgi()),  # WebSocket URL for timetable
    path('ws/notifications/', NotificationConsumer.as_asgi()),
]
