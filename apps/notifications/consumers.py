import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model
from .models import Notification

User = get_user_model()

class NotificationConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket URL: /ws/notifications/?token=<JWT>
    """

    async def connect(self):
        # Authenticate via token in query string
        token = self.scope["query_string"].decode().split("token=")[-1] if b"token=" in self.scope["query_string"] else None
        self.user = None
        if token:
            try:
                access = AccessToken(token)
                user_id = access.get("user_id")
                self.user = await database_sync_to_async(User.objects.get)(id=user_id)
            except Exception:
                self.user = None

        if not self.user:
            await self.close(code=4001)
            return

        self.group_name = f"user_{self.user.id}_notifications"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        # This consumer is read-only for notifications, so no receive handling needed
        pass

    async def send_notification(self, event):
        # Send notification data to WebSocket
        await self.send_json(event["content"])
