import logging

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import SecurityAlert
from .tasks import (broadcast_security_alert,refresh_security_alert_cache,)

# =========================================================
# LOGGER
# =========================================================

logger = logging.getLogger("security.signals")


# =========================================================
# SECURITY ALERT CREATED SIGNAL
# =========================================================

@receiver(post_save, sender=SecurityAlert)
def security_alert_created_handler(
    sender,
    instance,
    created,
    **kwargs
):

    if not created:
        return

    try:
        logger.info(
            "SecurityAlert created | alert_id=%s | user_id=%s | severity=%s",
            instance.id,
            instance.user_id,
            instance.severity,
        )

        # =================================================
        # WEBSOCKET BROADCAST (ASYNC VIA CELERY)
        # =================================================

        broadcast_security_alert.delay(instance.id)

        logger.info(
            "Broadcast task queued | alert_id=%s",
            instance.id,
        )

        # =================================================
        # CACHE REFRESH
        # =================================================

        refresh_security_alert_cache.delay()

        logger.info(
            "Cache refresh task queued | alert_id=%s",
            instance.id,
        )

    except Exception as exc:

        logger.exception(
            "SecurityAlert signal failed | alert_id=%s | error=%s",
            instance.id,
            str(exc),
        )