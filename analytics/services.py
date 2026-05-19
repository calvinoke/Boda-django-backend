# adminpanel/services.py

from django.core.cache import cache

from riders.models import RiderProfile

from verification.models import (
    RiderVerification
)

from announcements.models import (
    Announcement
)


# =========================================================
# CACHE SYSTEM STATS
# =========================================================

def cache_system_stats():

    stats = {

        "total_riders":
            RiderProfile.objects.count(),

        "approved_riders":
            RiderProfile.objects.filter(
                status='approved'
            ).count(),

        "pending_riders":
            RiderProfile.objects.filter(
                status='pending'
            ).count(),

        "suspended_riders":
            RiderProfile.objects.filter(
                status='suspended'
            ).count(),

        "verified_riders":
            RiderVerification.objects.filter(
                is_verified=True
            ).count(),

        "announcements":
            Announcement.objects.count(),
    }

    cache.set(
        "system_stats",
        stats,
        timeout=60 * 5
    )

    return stats