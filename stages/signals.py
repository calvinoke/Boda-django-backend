import logging
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Stage
from .tasks import broadcast_stage_update, refresh_stage_cache

logger = logging.getLogger("stages.signals")


# =========================================================
# STAGE CREATED / UPDATED SIGNAL (PRODUCTION READY)
# =========================================================

@receiver(post_save, sender=Stage)
def stage_saved_handler(sender, instance, created, **kwargs):

    try:

        event_type = "stage_created" if created else "stage_updated"

        message = {
            "event": event_type,
            "stage_id": instance.id,
            "name": instance.name,
            "district": instance.district,
            "division": instance.division,
        }

        # =====================================================
        # CELERY TASKS (ASYNC PROCESSING)
        # =====================================================

        broadcast_stage_update.delay(message)
        refresh_stage_cache.delay()

        # =====================================================
        # LOG SUCCESS
        # =====================================================

        logger.info(
            f"Stage signal processed | event={event_type} | stage_id={instance.id}"
        )

    except Exception as exc:

        # =====================================================
        # LOG FAILURE (CRITICAL FOR DEBUGGING IN PROD)
        # =====================================================

        logger.exception(
            f"Stage signal failed | stage_id={instance.id} | error={str(exc)}"
        )