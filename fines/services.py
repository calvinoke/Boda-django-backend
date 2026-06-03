import logging
from django.core.cache import cache
from .models import Fine


# =========================================================
# LOGGER
# =========================================================

logger = logging.getLogger("fines.cache")


# =========================================================
# CACHE UNPAID FINES COUNT
# =========================================================

def cache_unpaid_fines(user_id):

    try:
        total = Fine.objects.filter(
            status="pending",
            issued_by_id=user_id
        ).count()

        cache.set(
            f"unpaid_fines_{user_id}",
            total,
            timeout=3600
        )

        logger.info(
            f"Unpaid fines cached | user_id={user_id} | count={total}"
        )

        return total

    except Exception as exc:

        logger.error(
            f"Failed to cache unpaid fines | user_id={user_id} | error={str(exc)}"
        )

        return 0


# =========================================================
# CACHE RECENT FINES
# =========================================================

def cache_recent_fines():

    try:
        recent = list(
            Fine.objects.select_related(
                "rider",
                "guest_rider",
                "issued_by"
            )
            .order_by("-created_at")[:20]
            .values(
                "id",
                "amount",
                "status",
                "offender_type",
                "created_at",
                "rider_id",
                "guest_rider_id",
                "issued_by_id"
            )
        )

        cache.set(
            "recent_fines",
            recent,
            timeout=300
        )

        logger.info(
            f"Recent fines cached | count={len(recent)}"
        )

        return recent

    except Exception as exc:

        logger.error(
            f"Failed to cache recent fines | error={str(exc)}"
        )

        return []