from celery import shared_task
from django.core.cache import cache
from .services import (cache_rider_contacts)
from .models import EmergencyContact


# =========================================================
# REFRESH CONTACT CACHE
# =========================================================

@shared_task
def refresh_contact_cache(user_id):

    cache_rider_contacts(user_id)

    return "Contact cache refreshed"


# =========================================================
# DELETE CONTACT CACHE
# =========================================================

@shared_task
def clear_contact_cache(user_id):

    cache.delete(
        f"rider_contacts_{user_id}"
    )

    return "Contact cache cleared"


# =========================================================
# CACHE ALL CONTACTS COUNT
# =========================================================

@shared_task
def cache_total_contacts():

    total = EmergencyContact.objects.count()

    cache.set(

        "total_contacts",

        total,

        timeout=60 * 5
    )

    return total