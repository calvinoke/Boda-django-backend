from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import SecurityAlert
from .tasks import (

    broadcast_security_alert,

    refresh_security_alert_cache
)


# =========================================================
# SECURITY ALERT CREATED
# =========================================================

@receiver(post_save, sender=SecurityAlert)
def security_alert_created_handler(

    sender,

    instance,

    created,

    **kwargs
):

    if created:

        # =============================================
        # WEBSOCKET BROADCAST
        # =============================================

        broadcast_security_alert.delay(
            instance.id
        )

        # =============================================
        # REDIS CACHE REFRESH
        # =============================================

        refresh_security_alert_cache.delay()