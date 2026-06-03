import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger("verification.consumer")


class VerificationConsumer(AsyncWebsocketConsumer):

    # =====================================================
    # CONNECT
    # =====================================================

    async def connect(self):

        try:
            self.user = self.scope.get("user")

            # AUTH CHECK (CRITICAL FOR PRODUCTION)
            if not self.user or self.user.is_anonymous:
                logger.warning("Unauthorized WebSocket connection rejected")
                await self.close()
                return

            # USER-SPECIFIC ROOM (SAFER THAN GLOBAL ROOM)
            self.room_group_name = f"verification_{self.user.id}"

            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )

            await self.accept()

            logger.info(
                f"Verification WS connected | user_id={self.user.id}"
            )

        except Exception as exc:
            logger.exception(f"Verification connect error: {str(exc)}")
            await self.close()

    # =====================================================
    # DISCONNECT
    # =====================================================

    async def disconnect(self, close_code):

        try:
            if hasattr(self, "room_group_name"):
                await self.channel_layer.group_discard(
                    self.room_group_name,
                    self.channel_name
                )

            logger.info(
                f"Verification WS disconnected | user_id={getattr(self.user, 'id', None)}"
            )

        except Exception as exc:
            logger.exception(f"Verification disconnect error: {str(exc)}")

    # =====================================================
    # EVENT HANDLER
    # =====================================================

    async def send_verification_event(self, event):

        try:
            message = event.get("message", {})

            await self.send(
                text_data=json.dumps({
                    "message": message
                })
            )

            logger.info(
                f"Verification event sent | user_id={getattr(self.user, 'id', None)}"
            )

        except Exception as exc:
            logger.exception(f"Verification event send error: {str(exc)}")