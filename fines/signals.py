import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Fine
from .tasks import (
    broadcast_fine_alert,
    refresh_fines_cache
)


# =========================================================
# LOGGER
# =========================================================

logger = logging.getLogger("fines.signals")


# =========================================================
# FINE SIGNAL HANDLER
# =========================================================

@receiver(post_save, sender=Fine)
def fine_created_handler(sender, instance, created, **kwargs):

    try:

        # =================================================
        # OFFENDER RESOLUTION (SAFE)
        # =================================================

        offender_name = "Unknown"

        if instance.rider and getattr(instance.rider, "user", None):
            offender_name = getattr(
                instance.rider.user,
                "username",
                "Unknown"
            )

        elif instance.guest_rider and getattr(instance.guest_rider, "user", None):
            offender_name = getattr(
                instance.guest_rider.user,
                "username",
                "Unknown"
            )

        # =================================================
        # PAYLOAD
        # =================================================

        message = {
            "fine_id": instance.id,
            "offender_type": instance.offender_type,
            "offender_name": offender_name,
            "amount": str(instance.amount),
            "status": instance.status,
            "reason": instance.reason,
            "created_at": str(instance.created_at),
        }

        # =================================================
        # CREATE EVENT
        # =================================================

        if created:

            logger.info(
                f"Fine created | fine_id={instance.id} | offender={offender_name}"
            )

            broadcast_fine_alert.delay(message)

            logger.info(
                f"Fine broadcast triggered | fine_id={instance.id}"
            )

        # =================================================
        # UPDATE EVENT
        # =================================================

        else:

            logger.info(
                f"Fine updated | fine_id={instance.id} | status={instance.status}"
            )

        # =================================================
        # CACHE REFRESH (ALWAYS)
        # =================================================

        refresh_fines_cache.delay()

        logger.info(
            f"Fine cache refresh triggered | fine_id={instance.id} | created={created}"
        )

    except Exception as exc:

        logger.error(
            f"Fine signal failed | fine_id={getattr(instance, 'id', None)} | error={str(exc)}"
        )