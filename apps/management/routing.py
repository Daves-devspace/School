from django.urls import path
from .consumers import TimetableConsumer

websocket_urlpatterns = [
    path('ws/timetable/', TimetableConsumer.as_asgi()),  # WebSocket URL for timetable
]
