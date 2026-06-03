import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer


# =========================================================
# LOGGER
# =========================================================

logger = logging.getLogger("fines.websocket")


# =========================================================
# FINE CONSUMER
# =========================================================

class FineConsumer(AsyncWebsocketConsumer):

    async def connect(self):

        user = self.scope.get("user")

        # =================================================
        # AUTHENTICATION CHECK
        # =================================================

        if not user or not user.is_authenticated:

            logger.warning(
                "Unauthorized fine websocket connection attempt"
            )

            await self.close(code=4001)
            return

        self.user = user
        self.room_group_name = "fines"

        try:

            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )

            await self.accept()

            logger.info(
                f"Fine websocket connected | "
                f"user_id={user.id}"
            )

        except Exception as exc:

            logger.exception(
                f"Fine websocket connection failed | "
                f"user_id={user.id} | "
                f"error={str(exc)}"
            )

            await self.close()

    # =====================================================
    # DISCONNECT
    # =====================================================

    async def disconnect(self, close_code):

        try:

            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

            logger.info(
                f"Fine websocket disconnected | "
                f"user_id={getattr(self, 'user', None) and self.user.id} | "
                f"close_code={close_code}"
            )

        except Exception as exc:

            logger.exception(
                f"Fine websocket disconnect error | "
                f"error={str(exc)}"
            )

    # =====================================================
    # SEND FINE ALERT
    # =====================================================

    async def send_fine_alert(self, event):

        try:

            payload = {
                "message": event.get("message")
            }

            await self.send(
                text_data=json.dumps(payload)
            )

            logger.info(
                f"Fine alert delivered | "
                f"user_id={getattr(self, 'user', None) and self.user.id}"
            )

        except Exception as exc:

            logger.exception(
                f"Fine alert delivery failed | "
                f"user_id={getattr(self, 'user', None) and self.user.id} | "
                f"error={str(exc)}"
            )