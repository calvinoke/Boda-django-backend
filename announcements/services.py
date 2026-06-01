import logging
from django.core.cache import cache
from django.db import DatabaseError
from django.db.models import F
from .models import Announcement, Condolence


# =========================================================
# LOGGER
# =========================================================

logger = logging.getLogger("cache")


# =========================================================
# CACHE KEYS (VERSIONED)
# =========================================================

ANNOUNCEMENTS_CACHE_KEY = "v1_latest_announcements"
CONDOLENCES_CACHE_KEY = "v1_latest_condolences"

CACHE_LOCK_ANNOUNCEMENTS = "lock_cache_announcements"
CACHE_LOCK_CONDOLENCES = "lock_cache_condolences"


# =========================================================
# ANNOUNCEMENTS CACHE
# =========================================================

def cache_latest_announcements():

    # Prevent multiple workers from rebuilding cache at same time
    if cache.get(CACHE_LOCK_ANNOUNCEMENTS):
        logger.info("Announcements cache rebuild skipped (locked)")
        return

    cache.set(CACHE_LOCK_ANNOUNCEMENTS, True, timeout=30)

    try:
        logger.info("Refreshing announcements cache...")

        announcements = list(
            Announcement.objects.select_related("created_by")
            .order_by("-created_at")
            .values(
                "id",
                "title",
                "message",
                "announcement_type",
                "created_at",
            )[:50]
        )

        cache.set(
            ANNOUNCEMENTS_CACHE_KEY,
            announcements,
            timeout=60 * 10,  # 10 minutes
        )

        logger.info(f"Cached {len(announcements)} announcements successfully")

    except DatabaseError as e:
        logger.error(f"DB error while caching announcements: {str(e)}")

    except Exception as e:
        logger.exception(f"Unexpected error caching announcements: {str(e)}")

    finally:
        cache.delete(CACHE_LOCK_ANNOUNCEMENTS)


# =========================================================
# CONDOLENCES CACHE
# =========================================================

def cache_latest_condolences():

    if cache.get(CACHE_LOCK_CONDOLENCES):
        logger.info("Condolences cache rebuild skipped (locked)")
        return

    cache.set(CACHE_LOCK_CONDOLENCES, True, timeout=30)

    try:
        logger.info("Refreshing condolences cache...")

        condolences = list(
            Condolence.objects.select_related("rider")
            .order_by("-date_of_death")
            .values(
                "id",
                "description",
                "burial_location",
                "status",
                "date_of_death",
            )[:50]
        )

        cache.set(
            CONDOLENCES_CACHE_KEY,
            condolences,
            timeout=60 * 10,  # 10 minutes
        )

        logger.info(f"Cached {len(condolences)} condolences successfully")

    except DatabaseError as e:
        logger.error(f"DB error while caching condolences: {str(e)}")

    except Exception as e:
        logger.exception(f"Unexpected error caching condolences: {str(e)}")

    finally:
        cache.delete(CACHE_LOCK_CONDOLENCES)