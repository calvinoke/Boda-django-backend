from celery import shared_task
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.cache import cache
from .models import Stage


# =========================================================
# BROADCAST STAGE UPDATE
# =========================================================

@shared_task
def broadcast_stage_update(message):

    channel_layer = get_channel_layer()

    async_to_sync(
        channel_layer.group_send
    )(

        "stages",

        {

            "type": "send_stage_update",

            "message": message,
        }
    )


# =========================================================
# CACHE STAGES
# =========================================================

@shared_task
def refresh_stage_cache():

    stages = list(

        Stage.objects.select_related(
            'chairman',
            'secretary',
            'defense'
        ).values(

            'id',

            'name',

            'district',

            'division',

            'parish',

            'village',

            'is_active',

            'total_registered_riders',

            'total_guest_riders_seen',

            'suspicious_activity_score',

            'created_at'
        )
    )

    cache.set(

        "stages_cache",

        stages,

        timeout=60 * 10
    )

    return "Stage cache refreshed"