import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger("ws")


# =========================================================
# BASE CONSUMER (REUSABLE SECURITY LAYER)
# =========================================================

class BaseGroupConsumer(AsyncWebsocketConsumer):

    group_name = None

    async def connect(self):

        user = self.scope.get("user")

        # =====================================================
        # AUTH CHECK (IMPORTANT)
        # =====================================================
        if not user or not user.is_authenticated:
            logger.warning("Unauthorized WebSocket attempt blocked")
            await self.close()
            return

        self.user = user

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

        logger.info(
            f"WS connected | user={user.id} group={self.group_name}"
        )

    async def disconnect(self, close_code):

        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

        logger.info(
            f"WS disconnected | user={getattr(self, 'user', None)}"
        )

    async def safe_send(self, event):

        try:
            message = event.get("message", {})

            await self.send(
                text_data=json.dumps(message)
            )

        except Exception as e:
            logger.error(f"WS send error: {str(e)}")


# =========================================================
# ANNOUNCEMENT CONSUMER
# =========================================================

class AnnouncementConsumer(BaseGroupConsumer):

    group_name = "announcements"

    async def send_announcement(self, event):
        await self.safe_send(event)


# =========================================================
# CONDOLENCE CONSUMER
# =========================================================

class CondolenceConsumer(BaseGroupConsumer):

    group_name = "condolences"

    async def send_condolence(self, event):
        await self.safe_send(event)