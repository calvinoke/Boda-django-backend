import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Announcement, Condolence
from .tasks import (broadcast_announcement_task,broadcast_condolence_task,refresh_announcements_cache,refresh_condolences_cache,)

# =========================================================
# LOGGER
# =========================================================

logger = logging.getLogger("signals")


# =========================================================
# ANNOUNCEMENT CREATED
# =========================================================

@receiver(post_save, sender=Announcement)
def announcement_created_handler(sender, instance, created, **kwargs):

    if not created:
        return

    try:
        logger.info(f"Announcement created signal fired | id={instance.id}")

        broadcast_announcement_task.delay(instance.id)
        refresh_announcements_cache.delay()

        logger.info(f"Announcement tasks queued | id={instance.id}")

    except Exception as e:
        logger.exception(
            f"Announcement signal failure | id={instance.id} | error={str(e)}"
        )


# =========================================================
# CONDOLENCE CREATED
# =========================================================

@receiver(post_save, sender=Condolence)
def condolence_created_handler(sender, instance, created, **kwargs):

    if not created:
        return

    try:
        logger.info(f"Condolence created signal fired | id={instance.id}")

        broadcast_condolence_task.delay(instance.id)
        refresh_condolences_cache.delay()

        logger.info(f"Condolence tasks queued | id={instance.id}")

    except Exception as e:
        logger.exception(
            f"Condolence signal failure | id={instance.id} | error={str(e)}"
        )