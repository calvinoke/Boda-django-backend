import logging

from celery import shared_task
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.cache import cache
from .models import Stage


# =========================================================
# LOGGER
# =========================================================

logger = logging.getLogger("stages.tasks")


# =========================================================
# BROADCAST STAGE UPDATE
# =========================================================

@shared_task(bind=True, max_retries=3)
def broadcast_stage_update(self, message):

    try:

        logger.info(
            "Broadcasting stage update"
        )

        channel_layer = get_channel_layer()

        if not channel_layer:
            logger.error("Channel layer not configured")
            return "Channel layer missing"

        async_to_sync(channel_layer.group_send)(
            "stages",
            {
                "type": "send_stage_update",
                "message": message,
            },
        )

        logger.info(
            "Stage update broadcast successful"
        )

        return "Stage update broadcasted"

    except Exception as exc:

        logger.exception(
            "Stage broadcast failed | error=%s",
            str(exc),
        )

        raise self.retry(exc=exc, countdown=5)


# =========================================================
# CACHE STAGES
# =========================================================

@shared_task
def refresh_stage_cache():

    try:

        stages = list(
            Stage.objects.select_related(
                "chairman",
                "secretary",
                "defense",
            )
            .only(
                "id",
                "name",
                "district",
                "division",
                "parish",
                "village",
                "is_active",
                "total_registered_riders",
                "total_guest_riders_seen",
                "suspicious_activity_score",
                "created_at",
            )
            .values(
                "id",
                "name",
                "district",
                "division",
                "parish",
                "village",
                "is_active",
                "total_registered_riders",
                "total_guest_riders_seen",
                "suspicious_activity_score",
                "created_at",
            )
        )

        cache.set(
            "stages_cache",
            stages,
            timeout=60 * 10,
        )

        logger.info(
            "Stage cache refreshed | count=%s",
            len(stages),
        )

        return "Stage cache refreshed"

    except Exception as exc:

        logger.exception(
            "Stage cache refresh failed | error=%s",
            str(exc),
        )

        return "Stage cache refresh failed"