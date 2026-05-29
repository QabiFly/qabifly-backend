import json
from channels.generic.websocket import AsyncWebsocketConsumer


class SupportChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.ticket_number = self.scope["url_route"]["kwargs"]["ticket_number"]
        self.group_name    = f"support_{self.ticket_number}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type":        "chat_message",
                "message":     data.get("message", ""),
                "sender_type": data.get("sender_type", "USER"),
                "sender_name": data.get("sender_name", ""),
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "type":        "message",
            "message":     event["message"],
            "sender_type": event["sender_type"],
            "sender_name": event["sender_name"],
        }))