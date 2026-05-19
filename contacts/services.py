from django.core.cache import cache
from .models import EmergencyContact


# =========================================================
# CACHE CONTACTS
# =========================================================

def cache_rider_contacts(user_id):

    contacts = list(

        EmergencyContact.objects.filter(
            rider__user_id=user_id
        ).values(

            'id',

            'name',

            'phone_number',

            'relationship',

            'village'
        )
    )

    cache.set(

        f"rider_contacts_{user_id}",

        contacts,

        timeout=60 * 10
    )

    return contacts