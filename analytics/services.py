from django.core.cache import cache
from django.db.models import Count
from riders.models import RiderProfile
from verification.models import RiderVerification
from announcements.models import Announcement
import logging


# =========================================================
# LOGGER SETUP
# =========================================================

logger = logging.getLogger(__name__)


# =========================================================
# SYSTEM STATS CACHE SERVICE (PRODUCTION READY)
# =========================================================

def cache_system_stats():

    try:

        logger.info("Starting system stats cache computation")

        stats = RiderProfile.objects.aggregate(
            total_riders=Count('id'),
        )

        data = {

            # ================================
            # RIDER STATS
            # ================================

            "total_riders": stats["total_riders"],

            "approved_riders": RiderProfile.objects.filter(
                status='approved'
            ).count(),

            "pending_riders": RiderProfile.objects.filter(
                status='pending'
            ).count(),

            "suspended_riders": RiderProfile.objects.filter(
                status='suspended'
            ).count(),

            # ================================
            # VERIFICATION STATS
            # ================================

            "verified_riders": RiderVerification.objects.filter(
                is_verified=True
            ).count(),

            # ================================
            # ANNOUNCEMENTS
            # ================================

            "announcements": Announcement.objects.count(),
        }

        # ================================
        # CACHE STORAGE
        # ================================

        cache.set(
            "system_stats",
            data,
            timeout=60 * 5
        )

        logger.info("System stats cached successfully")

        return data

    except Exception as e:

        logger.error(
            f"System stats cache failed: {str(e)}",
            exc_info=True
        )

        cached = cache.get("system_stats")

        if cached:
            logger.warning("Returned stale cached system stats")
            return cached

        logger.critical("No cache fallback available for system stats")

        return {
            "error": "Unable to load system stats",
            "details": str(e)
        }