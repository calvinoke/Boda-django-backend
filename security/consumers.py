import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer


logger = logging.getLogger("security.websocket")


# =========================================================
# SECURITY ALERT CONSUMER
# =========================================================

class SecurityAlertConsumer(AsyncWebsocketConsumer):

    MAX_MESSAGE_SIZE = 5000

    # =====================================================
    # CONNECT
    # =====================================================

    async def connect(self):

        try:

            self.user = self.scope.get("user")

            if not self.user or self.user.is_anonymous:

                logger.warning(
                    "Security websocket rejected (anonymous user)"
                )

                await self.close(code=4001)
                return

            self.room_group_name = (
                f"security_alerts_{self.user.id}"
            )

            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )

            await self.accept()

            logger.info(
                f"Security websocket connected | "
                f"user_id={self.user.id}"
            )

        except Exception as exc:

            logger.error(
                f"Security websocket connect error | "
                f"error={str(exc)}"
            )

            await self.close(code=4500)

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
                f"Security websocket disconnected | "
                f"user_id={getattr(self.user, 'id', None)} | "
                f"code={close_code}"
            )

        except Exception as exc:

            logger.error(
                f"Security websocket disconnect error | "
                f"error={str(exc)}"
            )

    # =====================================================
    # RECEIVE FROM CLIENT
    # =====================================================

    async def receive(self, text_data=None, bytes_data=None):

        try:

            if not text_data:
                return

            if len(text_data) > self.MAX_MESSAGE_SIZE:

                logger.warning(
                    f"Security websocket payload too large | "
                    f"user_id={self.user.id}"
                )

                return

            try:

                payload = json.loads(text_data)

            except json.JSONDecodeError:

                logger.warning(
                    f"Invalid JSON received | "
                    f"user_id={self.user.id}"
                )

                return

            logger.info(
                f"Security websocket message received | "
                f"user_id={self.user.id}"
            )

            # Optional heartbeat support
            if payload.get("type") == "ping":

                await self.send(
                    text_data=json.dumps(
                        {
                            "type": "pong"
                        }
                    )
                )

        except Exception as exc:

            logger.error(
                f"Security websocket receive error | "
                f"user_id={getattr(self.user, 'id', None)} | "
                f"error={str(exc)}"
            )

    # =====================================================
    # SEND SECURITY ALERT
    # Called by Channels group_send()
    # =====================================================

    async def send_security_alert(self, event):

        try:

            data = event.get("data", {})

            await self.send(
                text_data=json.dumps(data)
            )

            logger.info(
                f"Security alert delivered | "
                f"user_id={self.user.id}"
            )

        except Exception as exc:

            logger.error(
                f"Security alert delivery failed | "
                f"user_id={getattr(self.user, 'id', None)} | "
                f"error={str(exc)}"
            )