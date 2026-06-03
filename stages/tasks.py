import logging

from celery import shared_task
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.cache import cache
from .models import Stage

logger = logging.getLogger("stages.tasks")


# =========================================================
# BROADCAST STAGE UPDATE (REAL-TIME)
# =========================================================

@shared_task(bind=True, max_retries=3)
def broadcast_stage_update(self, message):

    try:

        channel_layer = get_channel_layer()

        async_to_sync(channel_layer.group_send)(
            "stages",
            {
                "type": "send_stage_update",
                "message": message,
            }
        )

        logger.info(
            f"Stage broadcast sent | stage_id={message.get('stage_id')} | event={message.get('event')}"
        )

        return "Stage update broadcasted"

    except Exception as exc:

        logger.exception(
            f"Stage broadcast failed | error={str(exc)} | message={message}"
        )

        raise self.retry(exc=exc, countdown=5)


# =========================================================
# CACHE STAGES (OPTIMIZED SNAPSHOT CACHE)
# =========================================================

@shared_task
def refresh_stage_cache():

    try:

        stages = list(
            Stage.objects.select_related(
                'chairman',
                'secretary',
                'defense'
            ).values(
                'id',
                'name',
                'district',
                'division',
                'parish',
                'village',
                'is_active',
                'total_registered_riders',
                'total_guest_riders_seen',
                'suspicious_activity_score',
                'created_at'
            )
        )

        cache.set(
            "stages_cache",
            stages,
            timeout=60 * 10
        )

        logger.info(
            f"Stage cache refreshed | total_stages={len(stages)}"
        )

        return "Stage cache refreshed"

    except Exception as exc:

        logger.exception(
            f"Stage cache refresh failed | error={str(exc)}"
        )

        return "Cache refresh failed"