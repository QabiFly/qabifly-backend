from django.urls import path
from .consumers import SupportChatConsumer

websocket_urlpatterns = [
    path("ws/support/<str:ticket_number>/", SupportChatConsumer.as_asgi()),
]