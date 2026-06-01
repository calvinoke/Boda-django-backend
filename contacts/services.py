import logging
from django.core.cache import cache
from .models import EmergencyContact


# =========================================================
# LOGGER
# =========================================================

logger = logging.getLogger("cache")


# =========================================================
# CACHE CONTACTS (PRODUCTION SAFE)
# =========================================================

def cache_rider_contacts(user_id):

    cache_key = f"v1_rider_contacts_{user_id}"

    try:
        logger.info(f"Refreshing rider contacts cache | user_id={user_id}")

        contacts = list(
            EmergencyContact.objects.filter(
                rider__user_id=user_id
            ).values(
                "id",
                "name",
                "phone_number",
                "relationship",
                "village",
            )
        )

        cache.set(
            cache_key,
            contacts,
            timeout=60 * 10,  # 10 minutes
        )

        logger.info(
            f"Cached rider contacts successfully | user_id={user_id} | count={len(contacts)}"
        )

        return contacts

    except Exception as exc:

        logger.error(
            f"Failed to cache rider contacts | user_id={user_id} | error={str(exc)}"
        )

        # Safe fallback: still return fresh DB data
        try:
            return list(
                EmergencyContact.objects.filter(
                    rider__user_id=user_id
                ).values(
                    "id",
                    "name",
                    "phone_number",
                    "relationship",
                    "village",
                )
            )
        except Exception as inner_exc:
            logger.critical(
                f"Critical failure fetching rider contacts | user_id={user_id} | error={str(inner_exc)}"
            )
            return []