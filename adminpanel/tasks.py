import logging

from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.core.cache import cache

from .models import (
    RiderActivity,
    SystemLog
)

# =========================================================
# LOGGER
# =========================================================

logger = logging.getLogger(__name__)


# =========================================================
# BROADCAST ADMIN EVENT
# =========================================================

@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3}
)
def broadcast_admin_event(
    self,
    message
):

    try:

        channel_layer = get_channel_layer()

        if not channel_layer:

            logger.error(
                "Channel layer unavailable."
            )

            return

        async_to_sync(
            channel_layer.group_send
        )(
            "admin_dashboard",
            {
                "type": "send_admin_notification",
                "message": message,
            }
        )

        logger.info(
            f"Admin event broadcast successfully: {message}"
        )

    except Exception as exc:

        logger.exception(
            f"Failed to broadcast admin event: {str(exc)}"
        )

        raise


# =========================================================
# CACHE ADMIN STATS
# =========================================================

@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3}
)
def refresh_admin_cache(
    self
):

    try:

        activities = list(

            RiderActivity.objects
            .select_related("rider")
            .values(
                "id",
                "action",
                "description",
                "timestamp"
            )[:100]
        )

        logs = list(

            SystemLog.objects.values(
                "id",
                "message",
                "level",
                "created_at"
            )[:100]
        )

        cache.set(
            "admin_activities",
            activities,
            timeout=60 * 10
        )

        cache.set(
            "system_logs",
            logs,
            timeout=60 * 10
        )

        logger.info(
            "Admin cache refreshed successfully."
        )

        return {
            "status": "success",
            "activities": len(activities),
            "logs": len(logs)
        }

    except Exception as exc:

        logger.exception(
            f"Failed to refresh admin cache: {str(exc)}"
        )

        raise