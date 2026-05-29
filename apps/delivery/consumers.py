import json
from channels.generic.websocket import AsyncWebsocketConsumer


class DeliveryTrackingConsumer(AsyncWebsocketConsumer):
    """
    Real-time delivery tracking.
    Buyer connects → receives delivery boy GPS updates.
    Delivery boy sends location → broadcast to buyer.
    """

    async def connect(self):
        self.order_number = self.scope["url_route"]["kwargs"]["order_number"]
        self.group_name   = f"delivery_{self.order_number}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)

        if data.get("type") == "location_update":
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type":      "delivery_location",
                    "latitude":  data.get("latitude"),
                    "longitude": data.get("longitude"),
                    "timestamp": data.get("timestamp"),
                },
            )

    async def delivery_location(self, event):
        await self.send(text_data=json.dumps({
            "type":      "location_update",
            "latitude":  event["latitude"],
            "longitude": event["longitude"],
            "timestamp": event["timestamp"],
        }))