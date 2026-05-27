import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)


# =========================================================
# RATE LIMIT CONFIG
# =========================================================

RATE_LIMIT_SECONDS = 2  # prevent spam


def is_rate_limited(user_id, scope):
    """
    Simple Redis-backed rate limiter
    """

    key = f"ws_rate_limit:{scope}:{user_id}"
    last_time = cache.get(key)

    now = timezone.now().timestamp()

    if last_time and (now - last_time) < RATE_LIMIT_SECONDS:
        return True

    cache.set(key, now, timeout=RATE_LIMIT_SECONDS)
    return False


# =========================================================
# ADMIN DASHBOARD CONSUMER (PRODUCTION)
# =========================================================

class AdminDashboardConsumer(AsyncWebsocketConsumer):

    async def connect(self):

        try:
            user = self.scope["user"]

            # ============================
            # AUTHENTICATION CHECK
            # ============================
            if user.is_anonymous:
                await self.close(code=4001)
                return

            self.room_group_name = "admin_dashboard"
            self.user_id = user.id

            # ============================
            # RATE LIMIT CONNECTIONS
            # ============================
            if is_rate_limited(self.user_id, "admin_connect"):
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

            logger.info(f"AdminDashboard connected user={user.id}")

        except Exception as e:
            logger.error(f"Connect error: {str(e)}")
            await self.close()

    async def disconnect(self, close_code):

        try:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

            logger.info(
                f"AdminDashboard disconnected user={getattr(self.scope['user'], 'id', None)}"
            )

        except Exception as e:
            logger.error(f"Disconnect error: {str(e)}")

    async def send_admin_notification(self, event):

        try:

            user = self.scope["user"]

            # ============================
            # RATE LIMIT MESSAGES
            # ============================
            if is_rate_limited(user.id, "admin_notify"):
                return

            message = event.get("message", "")

            # ============================
            # SAFE JSON RESPONSE
            # ============================
            await self.send(text_data=json.dumps({
                "type": "admin_notification",
                "message": message
            }))

        except Exception as e:
            logger.error(f"send_admin_notification error: {str(e)}")