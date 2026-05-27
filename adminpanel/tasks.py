from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.core.cache import cache
from .models import ( RiderActivity, SystemLog)


# =========================================================
# BROADCAST ADMIN EVENT
# =========================================================

@shared_task
def broadcast_admin_event(message):

    channel_layer = get_channel_layer()

    async_to_sync(
        channel_layer.group_send
    )(

        "admin_dashboard",

        {

            "type": "send_admin_notification",

            "message": message,
        }
    )


# =========================================================
# CACHE ADMIN STATS
# =========================================================

@shared_task
def refresh_admin_cache():

    activities = list(

        RiderActivity.objects.select_related(
            'rider'
        ).values(

            'id',

            'action',

            'description',

            'timestamp'
        )[:100]
    )

    logs = list(

        SystemLog.objects.values(

            'id',

            'message',

            'level',

            'created_at'
        )[:100]
    )

    cache.set(

        "admin_activities",

        activities,

        timeout=60 * 10
    )

    cache.set(

        "system_logs",

        logs,

        timeout=60 * 10
    )

    return "Admin cache refreshed"