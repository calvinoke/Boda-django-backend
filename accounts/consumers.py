import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)


# =========================================================
# RATE LIMIT CONFIG
# =========================================================

RATE_LIMIT_SECONDS = 2


def is_rate_limited(user_id, scope):
    """
    Redis-based rate limiter to prevent spam messaging
    """

    key = f"ws_rate_limit:{scope}:{user_id}"
    last_time = cache.get(key)

    now = timezone.now().timestamp()

    if last_time and (now - last_time) < RATE_LIMIT_SECONDS:
        return True

    cache.set(key, now, timeout=RATE_LIMIT_SECONDS)
    return False


# =========================================================
# ACCOUNTS CONSUMER (PRODUCTION)
# =========================================================

class AccountsConsumer(AsyncWebsocketConsumer):

    # =====================================================
    # CONNECT
    # =====================================================
    async def connect(self):

        try:
            user = self.scope["user"]

            # ============================
            # AUTH CHECK
            # ============================
            if user.is_anonymous:
                await self.close(code=4001)
                return

            self.room_group_name = "accounts"
            self.user_id = user.id

            # ============================
            # RATE LIMIT CONNECTIONS
            # ============================
            if is_rate_limited(self.user_id, "accounts_connect"):
                await self.close(code=429)
                return

            # ============================
            # JOIN REDIS GROUP
            # ============================
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )

            await self.accept()

            logger.info(f"AccountsConsumer connected user={user.id}")

        except Exception as e:
            logger.error(f"Connect error: {str(e)}")
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
                f"AccountsConsumer disconnected user={getattr(self.scope['user'], 'id', None)}"
            )

        except Exception as e:
            logger.error(f"Disconnect error: {str(e)}")

    # =====================================================
    # RECEIVE MESSAGE FROM FRONTEND
    # =====================================================
    async def receive(self, text_data):

        try:

            user = self.scope["user"]

            # RATE LIMIT MESSAGES
            if is_rate_limited(user.id, "accounts_receive"):
                return

            data = json.loads(text_data or "{}")
            message = data.get("message", "").strip()

            if not message:
                return

            logger.info(f"Accounts message from user={user.id}: {message}")

            # SEND TO GROUP (REDIS BROADCAST)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "send_user_notification",
                    "message": message
                }
            )

        except json.JSONDecodeError:
            logger.error("Invalid JSON received in AccountsConsumer")

        except Exception as e:
            logger.error(f"Receive error: {str(e)}")

    # =====================================================
    # SEND MESSAGE TO FRONTEND
    # =====================================================
    async def send_user_notification(self, event):

        try:

            user = self.scope["user"]

            # RATE LIMIT OUTPUT
            if is_rate_limited(user.id, "accounts_notify"):
                return

            message = event.get("message", "")

            await self.send(text_data=json.dumps({
                "type": "user_notification",
                "message": message
            }))

        except Exception as e:
            logger.error(f"send_user_notification error: {str(e)}")