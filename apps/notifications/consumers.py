import json
from channels.generic.websocket import AsyncWebsocketConsumer


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    User connect karta hai → uske notifications real-time milte hain.
    ws/notifications/
    """

    async def connect(self):
        user = self.scope["user"]
        if not user or not user.is_authenticated:
            await self.close()
            return

        self.group_name = f"notifications_{user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def send_notification(self, event):
        await self.send(text_data=json.dumps({
            "type":       "notification",
            "id":         event["id"],
            "notif_type": event["notif_type"],
            "title":      event["title"],
            "body":       event["body"],
            "priority":   event["priority"],
            "data":       event["data"],
            "created_at": event["created_at"],
        }))