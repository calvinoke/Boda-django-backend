import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import RiderProfile, GuestRider
from .tasks import refresh_riders_cache, refresh_guest_riders_cache

logger = logging.getLogger("riders.signals")


# =========================================================
# RIDER PROFILE SIGNAL
# =========================================================

@receiver(post_save, sender=RiderProfile)
def rider_saved_handler(sender, instance, created, **kwargs):

    try:
        refresh_riders_cache.delay()

        logger.info(
            f"Rider cache refresh triggered | rider_id={instance.id} | created={created}"
        )

    except Exception as exc:
        logger.error(
            f"Rider signal failed | rider_id={instance.id} | error={str(exc)}"
        )


# =========================================================
# GUEST RIDER SIGNAL
# =========================================================

@receiver(post_save, sender=GuestRider)
def guest_rider_saved_handler(sender, instance, created, **kwargs):

    try:
        refresh_guest_riders_cache.delay()

        logger.info(
            f"Guest rider cache refresh triggered | guest_rider_id={instance.id} | created={created}"
        )

    except Exception as exc:
        logger.error(
            f"Guest rider signal failed | guest_rider_id={instance.id} | error={str(exc)}"
        )