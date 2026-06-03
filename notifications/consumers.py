import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger("notifications.ws")


class NotificationConsumer(AsyncWebsocketConsumer):

    async def connect(self):

        try:

            self.user = self.scope.get("user")

            # =============================================
            # AUTH CHECK
            # =============================================

            if not self.user or self.user.is_anonymous:
                logger.warning("WebSocket rejected (anonymous user)")
                await self.close()
                return

            self.room_group_name = f"notifications_{self.user.id}"

            # =============================================
            # JOIN GROUP
            # =============================================

            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )

            await self.accept()

            logger.info(f"WebSocket connected | user_id={self.user.id}")

        except Exception as exc:
            logger.error(f"WebSocket connect failed | error={str(exc)}")
            await self.close()

    async def disconnect(self, close_code):

        try:

            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

            logger.info(
                f"WebSocket disconnected | user_id={getattr(self.user, 'id', None)} | code={close_code}"
            )

        except Exception as exc:
            logger.error(f"WebSocket disconnect error | error={str(exc)}")

    # =============================================
    # SEND NOTIFICATION
    # =============================================

    async def send_notification(self, event):

        try:

            data = event.get("data", {})

            await self.send(
                text_data=json.dumps(data)
            )

            logger.debug(
                f"Notification sent | user_id={getattr(self.user, 'id', None)}"
            )

        except Exception as exc:
            logger.error(f"send_notification failed | error={str(exc)}")