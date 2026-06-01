import logging
from celery import shared_task
from django.core.cache import cache
from .services import cache_rider_contacts
from .models import EmergencyContact


# =========================================================
# LOGGER
# =========================================================

logger = logging.getLogger("celery")


# =========================================================
# REFRESH CONTACT CACHE
# =========================================================

@shared_task(bind=True, max_retries=3)
def refresh_contact_cache(self, user_id):

    try:
        logger.info(f"Refreshing contact cache | user_id={user_id}")

        result = cache_rider_contacts(user_id)

        logger.info(
            f"Contact cache refreshed successfully | user_id={user_id} | count={len(result)}"
        )

        return "Contact cache refreshed"

    except Exception as exc:

        logger.error(
            f"Contact cache refresh failed | user_id={user_id} | error={str(exc)}"
        )

        raise self.retry(exc=exc, countdown=5)


# =========================================================
# CLEAR CONTACT CACHE
# =========================================================

@shared_task
def clear_contact_cache(user_id):

    try:
        cache_key = f"rider_contacts_{user_id}"

        cache.delete(cache_key)

        logger.info(
            f"Contact cache cleared | user_id={user_id} | key={cache_key}"
        )

        return "Contact cache cleared"

    except Exception as exc:

        logger.error(
            f"Contact cache clear failed | user_id={user_id} | error={str(exc)}"
        )

        raise


# =========================================================
# CACHE TOTAL CONTACTS
# =========================================================

@shared_task
def cache_total_contacts():

    try:
        total = EmergencyContact.objects.count()

        cache.set(
            "total_contacts",
            total,
            timeout=60 * 5,
        )

        logger.info(
            f"Total contacts cached | count={total}"
        )

        return total

    except Exception as exc:

        logger.error(
            f"Failed to cache total contacts | error={str(exc)}"
        )

        raise