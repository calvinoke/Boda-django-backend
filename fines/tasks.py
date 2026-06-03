import logging
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
# LOGGER
# =========================================================

logger = logging.getLogger("fines.tasks")


# =========================================================
# BROADCAST LIVE FINE ALERT
# =========================================================

def offender_name_from_fine(fine):

    if fine.rider and getattr(fine.rider, "user", None):
        return getattr(fine.rider.user, "username", "Unknown")

    if fine.guest_rider and getattr(fine.guest_rider, "user", None):
        return getattr(fine.guest_rider.user, "username", "Unknown")

    return "Unknown"


# =========================================================
# BROADCAST TASK
# =========================================================

from celery import shared_task


@shared_task
def broadcast_fine_alert(fine_id):

    try:

        fine = Fine.objects.select_related(
            "rider",
            "guest_rider",
            "fine_type",
            "issued_by",
            "stage"
        ).get(id=fine_id)

        offender_name = offender_name_from_fine(fine)

        channel_layer = get_channel_layer()

        payload = {
            "fine_id": fine.id,
            "offender_type": fine.offender_type,
            "offender_name": offender_name,
            "fine_type": fine.fine_type.name if fine.fine_type else None,
            "amount": str(fine.amount),
            "reason": fine.reason,
            "status": fine.status,
            "stage": fine.stage.name if fine.stage else None,
            "issued_by": fine.issued_by.username if fine.issued_by else "System",
            "created_at": fine.created_at.isoformat(),
        }

        async_to_sync(channel_layer.group_send)(
            "fines",
            {
                "type": "send_fine_alert",
                "message": payload,
            }
        )

        logger.info(f"Fine broadcast success | fine_id={fine.id}")

        return f"Fine alert broadcasted: {fine.id}"

    except Fine.DoesNotExist:

        logger.warning(f"Fine not found | fine_id={fine_id}")

        return "Fine does not exist"

    except Exception as exc:

        logger.error(
            f"Fine broadcast failed | fine_id={fine_id} | error={str(exc)}"
        )

        raise


# =========================================================
# REFRESH CACHE
# =========================================================

@shared_task
def refresh_fines_cache(user_id=None):

    try:

        cache_recent_fines()

        if user_id:
            cache_unpaid_fines(user_id)

        logger.info(f"Fine cache refreshed | user_id={user_id}")

        return "Fine cache refreshed"

    except Exception as exc:

        logger.error(f"Cache refresh failed | error={str(exc)}")
        raise


# =========================================================
# AUTO CLOSE DISPUTES (OPTIMIZED)
# =========================================================

@shared_task
def auto_close_old_disputes():

    try:

        cutoff_date = timezone.now() - timedelta(days=7)

        updated_count = Fine.objects.filter(
            status="disputed",
            created_at__lte=cutoff_date
        ).update(status="pending")

        logger.info(f"Disputes auto-closed | count={updated_count}")

        return f"{updated_count} disputed fines reset to pending"

    except Exception as exc:

        logger.error(f"Auto close disputes failed | error={str(exc)}")
        raise


# =========================================================
# CACHE UNPAID COUNT
# =========================================================

@shared_task
def cache_unpaid_fines_count():

    try:

        unpaid_count = Fine.objects.filter(
            status="pending"
        ).count()

        cache.set(
            "unpaid_fines_count",
            unpaid_count,
            timeout=300
        )

        logger.info(f"Unpaid fines cached | count={unpaid_count}")

        return unpaid_count

    except Exception as exc:

        logger.error(f"Unpaid fines cache failed | error={str(exc)}")
        raise


# =========================================================
# CLEANUP OLD PAID FINES
# =========================================================

@shared_task
def cleanup_old_paid_fines():

    try:

        cutoff_date = timezone.now() - timedelta(days=365)

        deleted_count, _ = Fine.objects.filter(
            status="paid",
            created_at__lte=cutoff_date
        ).delete()

        logger.info(f"Old paid fines deleted | count={deleted_count}")

        return f"{deleted_count} old paid fines deleted"

    except Exception as exc:

        logger.error(f"Cleanup failed | error={str(exc)}")
        raise