import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import EmergencyContact
from .tasks import (refresh_contact_cache,clear_contact_cache,cache_total_contacts,)

logger = logging.getLogger("signals")


# =========================================================
# SAVE SIGNAL
# =========================================================

@receiver(post_save, sender=EmergencyContact)
def contact_saved(sender, instance, created, **kwargs):

    try:
        user_id = getattr(instance.rider.user, "id", None)

        if not user_id:
            logger.warning(
                f"Contact save signal skipped (missing user) | contact_id={instance.id}"
            )
            return

        logger.info(
            f"Contact saved signal fired | contact_id={instance.id} | user_id={user_id}"
        )

        refresh_contact_cache.delay(user_id)
        cache_total_contacts.delay()

        logger.info(
            f"Contact cache refresh queued | user_id={user_id}"
        )

    except Exception as exc:

        logger.error(
            f"Contact save signal failed | contact_id={instance.id} | error={str(exc)}"
        )


# =========================================================
# DELETE SIGNAL
# =========================================================

@receiver(post_delete, sender=EmergencyContact)
def contact_deleted(sender, instance, **kwargs):

    try:
        user_id = getattr(instance.rider.user, "id", None)

        if not user_id:
            logger.warning(
                f"Contact delete signal skipped (missing user) | contact_id={instance.id}"
            )
            return

        logger.info(
            f"Contact deleted signal fired | contact_id={instance.id} | user_id={user_id}"
        )

        clear_contact_cache.delay(user_id)
        cache_total_contacts.delay()

        logger.info(
            f"Contact cache clear queued | user_id={user_id}"
        )

    except Exception as exc:

        logger.error(
            f"Contact delete signal failed | contact_id={instance.id} | error={str(exc)}"
        )