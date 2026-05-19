from django.db.models.signals import post_save

from django.dispatch import receiver

from .models import Fine

from .tasks import (
    broadcast_fine_alert,
    refresh_fines_cache
)


# =========================================================
# FINE CREATED SIGNAL
# =========================================================

@receiver(post_save, sender=Fine)
def fine_created_handler(
    sender,
    instance,
    created,
    **kwargs
):

    # =====================================================
    # ONLY RUN WHEN NEW FINE IS CREATED
    # =====================================================

    if created:

        # =================================================
        # GET OFFENDER NAME
        # =================================================

        offender_name = "Unknown"

        if instance.rider:

            offender_name = (
                instance.rider.user.username
            )

        elif instance.guest_rider:

            offender_name = (
                instance.guest_rider.user.username
            )

        # =================================================
        # CREATE REALTIME ALERT MESSAGE
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
        # BROADCAST USING CELERY + REDIS CHANNELS
        # =================================================

        broadcast_fine_alert.delay(message)

        # =================================================
        # REFRESH REDIS CACHE
        # =================================================

        refresh_fines_cache.delay()

    # =====================================================
    # WHEN FINE IS UPDATED
    # =====================================================

    else:

        refresh_fines_cache.delay()