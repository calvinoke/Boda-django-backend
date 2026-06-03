import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import RiderVerification, VerificationRequest
from .tasks import (broadcast_verification_event,refresh_verification_cache)

logger = logging.getLogger("verification.signals")


# =========================================================
# RIDER VERIFICATION SIGNAL
# =========================================================

@receiver(post_save, sender=RiderVerification)
def verification_saved_handler(sender, instance, created, **kwargs):

    try:
        rider_username = (
            instance.rider.user.username
            if instance.rider and instance.rider.user
            else "unknown"
        )

        message = {
            "event": "verification_created" if created else "verification_updated",
            "verification_id": instance.id,
            "rider": rider_username,
            "is_verified": instance.is_verified,
        }

        broadcast_verification_event.delay(message)
        refresh_verification_cache.delay()

        logger.info(
            "Verification event sent | verification_id=%s | event=%s",
            instance.id,
            message["event"]
        )

    except Exception as e:
        logger.exception(
            "Failed in RiderVerification signal | verification_id=%s | error=%s",
            instance.id,
            str(e)
        )


# =========================================================
# VERIFICATION REQUEST SIGNAL
# =========================================================

@receiver(post_save, sender=VerificationRequest)
def verification_request_handler(sender, instance, created, **kwargs):

    try:
        username = (
            instance.user.username
            if instance.user
            else "unknown"
        )

        if created:

            message = {
                "event": "verification_request_created",
                "request_id": instance.id,
                "username": username,
            }

            broadcast_verification_event.delay(message)

            logger.info(
                "Verification request created | request_id=%s | user=%s",
                instance.id,
                username
            )

    except Exception as e:
        logger.exception(
            "Failed in VerificationRequest signal | request_id=%s | error=%s",
            instance.id,
            str(e)
        )