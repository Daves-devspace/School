from django.core.asgi import get_asgi_application
from django.urls import path
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from .consumers import AppointmentCountConsumer, InboxConsumer

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter([
            path("ws/inbox/", InboxConsumer.as_asgi()),
            path("ws/appointments/", AppointmentCountConsumer.as_asgi()),
        ])
    ),
})
