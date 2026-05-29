from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path("ws/delivery/<str:order_number>/", consumers.DeliveryTrackingConsumer.as_asgi()),
]