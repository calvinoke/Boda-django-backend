from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import (

    RiderVerification,

    VerificationRequest
)
from .tasks import (

    broadcast_verification_event,

    refresh_verification_cache
)


# =========================================================
# RIDER VERIFICATION SIGNAL
# =========================================================

@receiver(post_save, sender=RiderVerification)
def verification_saved_handler(
    sender,
    instance,
    created,
    **kwargs
):

    if created:

        message = {

            "event": "verification_created",

            "verification_id": instance.id,

            "rider": instance.rider.user.username,
        }

    else:

        message = {

            "event": "verification_updated",

            "verification_id": instance.id,

            "rider": instance.rider.user.username,

            "is_verified": instance.is_verified,
        }

    broadcast_verification_event.delay(message)

    refresh_verification_cache.delay()


# =========================================================
# VERIFICATION REQUEST SIGNAL
# =========================================================

@receiver(post_save, sender=VerificationRequest)
def verification_request_handler(
    sender,
    instance,
    created,
    **kwargs
):

    if created:

        broadcast_verification_event.delay({

            "event": "verification_request_created",

            "request_id": instance.id,

            "username": instance.user.username,
        })