from django.core.cache import cache

from .models import Fine


# =========================================================
# CACHE UNPAID FINES COUNT
# =========================================================

def cache_unpaid_fines(user_id):

    total = Fine.objects.filter(
        status='pending'
    ).count()

    cache.set(
        f'unpaid_fines_{user_id}',
        total,
        timeout=3600
    )

    return total


# =========================================================
# CACHE RECENT FINES
# =========================================================

def cache_recent_fines():

    recent = list(

        Fine.objects.select_related(
            'rider',
            'guest_rider'
        ).order_by('-created_at')[:20].values()
    )

    cache.set(
        'recent_fines',
        recent,
        timeout=300
    )

    return recent