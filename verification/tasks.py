import logging

from celery import shared_task
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.cache import cache
from django.utils import timezone
from .models import RiderVerification, VerificationRequest

logger = logging.getLogger("verification.tasks")


# =========================================================
# BROADCAST VERIFICATION EVENT
# =========================================================

@shared_task
def broadcast_verification_event(message):

    try:
        channel_layer = get_channel_layer()

        async_to_sync(channel_layer.group_send)(
            "verification",
            {
                "type": "send_verification_event",
                "message": message,
            }
        )

        logger.info(
            "Verification broadcast sent | event=%s",
            message.get("event", "unknown")
        )

    except Exception as e:
        logger.exception(
            "Failed to broadcast verification event | error=%s | message=%s",
            str(e),
            message
        )


# =========================================================
# REFRESH REDIS CACHE
# =========================================================

@shared_task
def refresh_verification_cache():

    try:
        verifications = list(
            RiderVerification.objects.select_related(
                'rider',
                'verified_by'
            ).values(
                'id',
                'rider_id',
                'is_verified',
                'verified_at',
                'submitted_at'
            )
        )

        cache.set(
            "verification_cache",
            verifications,
            timeout=60 * 10
        )

        logger.info(
            "Verification cache refreshed | count=%s",
            len(verifications)
        )

        return "Verification cache refreshed"

    except Exception as e:
        logger.exception(
            "Failed to refresh verification cache | error=%s",
            str(e)
        )


# =========================================================
# AUTO APPROVE TASK
# =========================================================

@shared_task
def approve_verification_task(
    verification_request_id,
    admin_user_id
):

    try:
        request = VerificationRequest.objects.select_related(
            'user'
        ).get(id=verification_request_id)

        verification = RiderVerification.objects.select_related(
            'rider'
        ).get(rider__user=request.user)

        # =================================================
        # UPDATE VERIFICATION
        # =================================================

        verification.is_verified = True
        verification.verified_by_id = admin_user_id
        verification.verified_at = timezone.now()
        verification.save()

        # =================================================
        # UPDATE REQUEST
        # =================================================

        request.status = "approved"
        request.save()

        logger.info(
            "Verification approved | request_id=%s | user_id=%s | admin_id=%s",
            request.id,
            request.user_id,
            admin_user_id
        )

        # =================================================
        # WEBSOCKET BROADCAST
        # =================================================

        broadcast_verification_event.delay({
            "event": "verification_approved",
            "user_id": request.user.id,
            "username": request.user.username,
        })

        refresh_verification_cache.delay()

        return "Verification approved successfully"

    except VerificationRequest.DoesNotExist:
        logger.warning(
            "Verification request not found | id=%s",
            verification_request_id
        )

    except RiderVerification.DoesNotExist:
        logger.warning(
            "Rider verification not found for request | request_id=%s",
            verification_request_id
        )

    except Exception as e:
        logger.exception(
            "Unexpected error in approve_verification_task | request_id=%s | error=%s",
            verification_request_id,
            str(e)
        )