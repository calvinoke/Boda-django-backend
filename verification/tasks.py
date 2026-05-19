from celery import shared_task
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.cache import cache
from django.utils import timezone
from .models import (

    RiderVerification,

    VerificationRequest
)


# =========================================================
# BROADCAST VERIFICATION EVENT
# =========================================================

@shared_task
def broadcast_verification_event(message):

    channel_layer = get_channel_layer()

    async_to_sync(
        channel_layer.group_send
    )(

        "verification",

        {

            "type": "send_verification_event",

            "message": message,
        }
    )


# =========================================================
# REFRESH REDIS CACHE
# =========================================================

@shared_task
def refresh_verification_cache():

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

    return "Verification cache refreshed"


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

        verification = RiderVerification.objects.get(
            rider__user=request.user
        )

        verification.is_verified = True

        verification.verified_by_id = admin_user_id

        verification.verified_at = timezone.now()

        verification.save()

        request.status = "approved"

        request.save()

        # =================================================
        # WEBSOCKET BROADCAST
        # =================================================

        broadcast_verification_event.delay({

            "event": "verification_approved",

            "user_id": request.user.id,

            "username": request.user.username,
        })

        refresh_verification_cache.delay()

    except Exception as e:

        print(str(e))