from celery import shared_task

from asgiref.sync import async_to_sync

from channels.layers import get_channel_layer

from django.core.cache import cache

from django.utils import timezone

from datetime import timedelta

from .models import Fine

from .services import (
    cache_recent_fines,
    cache_unpaid_fines
)


# =========================================================
# BROADCAST LIVE FINE ALERT
# =========================================================

@shared_task
def broadcast_fine_alert(fine_id):

    try:

        fine = Fine.objects.select_related(
            'rider',
            'guest_rider',
            'fine_type',
            'issued_by'
        ).get(id=fine_id)

        # =================================================
        # GET OFFENDER NAME
        # =================================================

        offender_name = "Unknown"

        if fine.rider:

            offender_name = (
                fine.rider.user.username
            )

        elif fine.guest_rider:

            offender_name = (
                fine.guest_rider.user.username
            )

        # =================================================
        # REDIS CHANNEL LAYER
        # =================================================

        channel_layer = get_channel_layer()

        async_to_sync(
            channel_layer.group_send
        )(

            "fines",

            {

                "type": "send_fine_alert",

                "message": {

                    "fine_id": fine.id,

                    "offender_type": fine.offender_type,

                    "offender_name": offender_name,

                    "fine_type": (
                        fine.fine_type.name
                        if fine.fine_type
                        else None
                    ),

                    "amount": str(fine.amount),

                    "reason": fine.reason,

                    "status": fine.status,

                    "stage": (
                        fine.stage.name
                        if fine.stage
                        else None
                    ),

                    "issued_by": (
                        fine.issued_by.username
                        if fine.issued_by
                        else "System"
                    ),

                    "created_at": (
                        fine.created_at.isoformat()
                    ),
                }
            }
        )

        return f"Fine alert broadcasted: {fine.id}"

    except Fine.DoesNotExist:

        return "Fine does not exist"


# =========================================================
# REFRESH REDIS CACHE
# =========================================================

@shared_task
def refresh_fines_cache(user_id=None):

    # =====================================================
    # CACHE RECENT FINES
    # =====================================================

    cache_recent_fines()

    # =====================================================
    # CACHE USER UNPAID FINES
    # =====================================================

    if user_id:

        cache_unpaid_fines(user_id)

    # =====================================================
    # GLOBAL CACHE
    # =====================================================

    fines = list(

        Fine.objects.select_related(
            'rider',
            'guest_rider',
            'fine_type'
        ).values(

            'id',

            'amount',

            'status',

            'offender_type',

            'reason',

            'created_at'
        )[:100]
    )

    cache.set(

        "recent_fines",

        fines,

        timeout=60 * 10
    )

    return "Fine cache refreshed"


# =========================================================
# AUTO CLOSE OLD DISPUTED FINES
# =========================================================

@shared_task
def auto_close_old_disputes():

    # =====================================================
    # FIND OLD DISPUTED FINES
    # =====================================================

    cutoff_date = timezone.now() - timedelta(days=7)

    old_fines = Fine.objects.filter(

        status='disputed',

        created_at__lte=cutoff_date
    )

    updated_count = 0

    for fine in old_fines:

        fine.status = 'pending'

        fine.save()

        updated_count += 1

    return f"{updated_count} disputed fines reset to pending"


# =========================================================
# CACHE UNPAID FINES COUNT
# =========================================================

@shared_task
def cache_unpaid_fines_count():

    unpaid_count = Fine.objects.filter(
        status='pending'
    ).count()

    cache.set(

        "unpaid_fines_count",

        unpaid_count,

        timeout=60 * 5
    )

    return unpaid_count


# =========================================================
# DELETE VERY OLD PAID FINES
# =========================================================

@shared_task
def cleanup_old_paid_fines():

    cutoff_date = timezone.now() - timedelta(days=365)

    deleted_count, _ = Fine.objects.filter(

        status='paid',

        created_at__lte=cutoff_date

    ).delete()

    return f"{deleted_count} old paid fines deleted"