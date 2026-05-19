from celery import shared_task
from django.core.cache import cache
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils import timezone
from .models import (
    RiderProfile,
    GuestRider
)


# =========================================================
# TEST TASK
# =========================================================

@shared_task
def test_task():

    return "Celery is working!"


# =========================================================
# CACHE RIDERS
# =========================================================

@shared_task
def refresh_riders_cache():

    riders = list(

        RiderProfile.objects.select_related(
            'user',
            'stage'
        ).values(

            'id',

            'user__username',

            'bike_plate_number',

            'status',

            'is_online',

            'is_verified',

            'latitude',

            'longitude'
        )
    )

    cache.set(

        "active_riders",

        riders,

        timeout=60 * 10
    )

    return "Riders cache refreshed"


# =========================================================
# CACHE GUEST RIDERS
# =========================================================

@shared_task
def refresh_guest_riders_cache():

    guests = list(

        GuestRider.objects.select_related(
            'user'
        ).values(

            'id',

            'user__username',

            'bike_plate_number',

            'status',

            'latitude',

            'longitude'
        )
    )

    cache.set(

        "guest_riders",

        guests,

        timeout=60 * 10
    )

    return "Guest riders cache refreshed"


# =========================================================
# UPDATE RIDER ONLINE STATUS
# =========================================================

@shared_task
def set_rider_online_status(

    rider_id,

    status=True
):

    try:

        rider = RiderProfile.objects.get(
            id=rider_id
        )

        rider.is_online = status

        rider.last_location_update = timezone.now()

        rider.save()

        # =============================================
        # BROADCAST LIVE STATUS
        # =============================================

        channel_layer = get_channel_layer()

        async_to_sync(
            channel_layer.group_send
        )(

            "riders",

            {

                "type": "send_rider_status",

                "data": {

                    "rider_id": rider.id,

                    "username": rider.user.username,

                    "is_online": rider.is_online,
                }
            }
        )

        return "Rider status updated"

    except RiderProfile.DoesNotExist:

        return "Rider not found"