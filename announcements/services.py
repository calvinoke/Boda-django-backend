from django.core.cache import cache
from .models import (Announcement,Condolence)


# =========================================================
# CACHE ANNOUNCEMENTS
# =========================================================

def cache_latest_announcements():

    announcements = list(

        Announcement.objects.select_related(
            'created_by'
        ).values(

            'id',
            'title',
            'message',
            'announcement_type',
            'created_at'
        )[:50]
    )

    cache.set(
        "latest_announcements",
        announcements,
        timeout=60 * 10
    )


# =========================================================
# CACHE CONDOLENCES
# =========================================================

def cache_latest_condolences():

    condolences = list(

        Condolence.objects.select_related(
            'rider'
        ).values(

            'id',
            'description',
            'burial_location',
            'status',
            'date_of_death'
        )[:50]
    )

    cache.set(
        "latest_condolences",
        condolences,
        timeout=60 * 10
    )