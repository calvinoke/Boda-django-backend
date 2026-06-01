import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.cache import cache

logger = logging.getLogger("emergency_ws")


class EmergencyContactConsumer(AsyncWebsocketConsumer):

    # =====================================================
    # CONNECT (AUTH REQUIRED)
    # =====================================================

    async def connect(self):

        user = self.scope.get("user")

        if not user or not user.is_authenticated:
            logger.warning("Unauthorized WebSocket connection attempt blocked")
            await self.close()
            return

        self.user = user
        self.room_group_name = "emergency_contacts"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )

        await self.accept()

        logger.info(
            f"WebSocket connected | user_id={user.id} group={self.room_group_name}"
        )

    # =====================================================
    # DISCONNECT
    # =====================================================

    async def disconnect(self, close_code):

        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name,
        )

        logger.info(
            f"WebSocket disconnected | user_id={getattr(self, 'user', None)} | code={close_code}"
        )

    # =====================================================
    # RECEIVE MESSAGE (SAFE + VALIDATED)
    # =====================================================

    async def receive(self, text_data):

        user = self.scope.get("user")

        if not user or not user.is_authenticated:
            logger.warning("Unauthenticated message attempt blocked")
            await self.close()
            return

        # =================================================
        # RATE LIMITING
        # =================================================

        key = f"emergency_rate:{user.id}"
        count = cache.get(key, 0)

        if count > 20:
            logger.warning(f"Rate limit exceeded | user_id={user.id}")
            await self.close()
            return

        cache.set(key, count + 1, timeout=60)

        # =================================================
        # JSON PARSING
        # =================================================

        try:
            data = json.loads(text_data)

        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON received | user_id={user.id}")
            return

        message = data.get("message")

        # =================================================
        # VALIDATION
        # =================================================

        if not message or not isinstance(message, str):
            logger.warning(f"Invalid message format | user_id={user.id}")
            return

        if len(message) > 500:
            logger.warning(f"Message too long | user_id={user.id}")
            return

        # =================================================
        # BROADCAST
        # =================================================

        logger.info(f"Emergency alert broadcast | user_id={user.id}")

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "send_contact_alert",
                "message": message,
                "user_id": user.id,
            },
        )

    # =====================================================
    # SEND TO CLIENT
    # =====================================================

    async def send_contact_alert(self, event):

        await self.send(
            text_data=json.dumps(
                {
                    "message": event.get("message"),
                    "user_id": event.get("user_id"),
                }
            )
        )

        logger.info(
            f"Emergency alert delivered | user_id={event.get('user_id')}"
        )