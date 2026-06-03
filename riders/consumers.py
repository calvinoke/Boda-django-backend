import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger("riders.ws")


class RiderConsumer(AsyncWebsocketConsumer):

    async def connect(self):

        try:

            self.user = self.scope.get("user")

            # =========================================
            # AUTH CHECK (SAFETY)
            # =========================================

            if not self.user or self.user.is_anonymous:
                logger.warning("Rejected rider WS connection (anonymous user)")
                await self.close()
                return

            self.room_group_name = "riders"

            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )

            await self.accept()

            logger.info(
                f"Rider WS connected | user_id={self.user.id}"
            )

        except Exception as exc:
            logger.error(
                f"Rider WS connect failed | error={str(exc)}"
            )
            await self.close()

    async def disconnect(self, close_code):

        try:

            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

            logger.info(
                f"Rider WS disconnected | user_id={getattr(self.user, 'id', None)} | code={close_code}"
            )

        except Exception as exc:
            logger.error(
                f"Rider WS disconnect error | error={str(exc)}"
            )

    # =====================================================
    # SEND LIVE RIDER STATUS
    # =====================================================

    async def send_rider_status(self, event):

        try:

            data = event.get("data", {})

            await self.send(
                text_data=json.dumps(data)
            )

            logger.debug(
                f"Rider status sent | user_id={getattr(self.user, 'id', None)}"
            )

        except Exception as exc:
            logger.error(
                f"send_rider_status failed | error={str(exc)}"
            )