import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)


# =========================================================
# RATE LIMIT HELPERS (USING REDIS CACHE)
# =========================================================

RATE_LIMIT_SECONDS = 2  # 1 message per 2 seconds per user


def is_rate_limited(user_id, scope):
    """
    Simple Redis-based rate limiter.
    Prevents spam WebSocket connections/messages.
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

class AnalyticsDashboardConsumer(AsyncWebsocketConsumer):

    async def connect(self):

        try:
            user = self.scope["user"]

            # ===============================
            # AUTHENTICATION CHECK
            # ===============================
            if user.is_anonymous:
                await self.close()
                return

            self.room_group_name = "admin_dashboard"
            self.user_id = user.id

            # ===============================
            # RATE LIMIT CONNECTIONS
            # ===============================
            if is_rate_limited(self.user_id, "connect"):
                await self.close(code=429)
                return

            # ===============================
            # JOIN GROUP (REDIS BACKEND)
            # ===============================
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )

            await self.accept()

            logger.info(f"WebSocket connected: admin_dashboard user={user.id}")

        except Exception as e:
            logger.error(f"WebSocket connect error: {str(e)}")
            await self.close()

    async def disconnect(self, close_code):

        try:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

            logger.info(f"WebSocket disconnected: admin_dashboard user={getattr(self.scope['user'], 'id', None)}")

        except Exception as e:
            logger.error(f"Disconnect error: {str(e)}")

    async def send_admin_update(self, event):

        try:

            # ===============================
            # RATE LIMIT MESSAGES
            # ===============================
            user = self.scope["user"]

            if is_rate_limited(user.id, "admin_update"):
                return

            message = event.get("message", {})

            await self.send(text_data=json.dumps({
                "type": "admin_update",
                "data": message
            }))

        except Exception as e:
            logger.error(f"send_admin_update error: {str(e)}")


# =========================================================
# SYSTEM STATS CONSUMER (PRODUCTION)
# =========================================================

class SystemStatsConsumer(AsyncWebsocketConsumer):

    async def connect(self):

        try:
            user = self.scope["user"]

            # AUTH CHECK
            if user.is_anonymous:
                await self.close()
                return

            self.room_group_name = "admin_stats"
            self.user_id = user.id

            # RATE LIMIT
            if is_rate_limited(self.user_id, "stats_connect"):
                await self.close(code=429)
                return

            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )

            await self.accept()

            logger.info(f"WebSocket connected: admin_stats user={user.id}")

        except Exception as e:
            logger.error(f"Stats connect error: {str(e)}")
            await self.close()

    async def disconnect(self, close_code):

        try:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

            logger.info(f"WebSocket disconnected: admin_stats user={getattr(self.scope['user'], 'id', None)}")

        except Exception as e:
            logger.error(f"Stats disconnect error: {str(e)}")

    async def send_stats_update(self, event):

        try:

            user = self.scope["user"]

            if is_rate_limited(user.id, "stats_update"):
                return

            message = event.get("message", {})

            await self.send(text_data=json.dumps({
                "type": "stats_update",
                "data": message
            }))

        except Exception as e:
            logger.error(f"send_stats_update error: {str(e)}")