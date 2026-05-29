import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from apps.delivery.routing import websocket_urlpatterns as delivery_ws
from apps.notifications.routing import websocket_urlpatterns as notification_ws
from apps.support.routing import websocket_urlpatterns as support_ws

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            delivery_ws + notification_ws + support_ws
        )
    ),
})