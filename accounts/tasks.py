from celery import shared_task
from channels.layers import (
    get_channel_layer
)

from asgiref.sync import (
    async_to_sync
)
from django.core.cache import cache
from .models import User


# =========================================================
# BROADCAST USER EVENT
# =========================================================

@shared_task
def broadcast_user_event(message):

    channel_layer = get_channel_layer()

    async_to_sync(
        channel_layer.group_send
    )(

        "accounts",

        {

            "type": "send_user_notification",

            "message": message,
        }
    )


# =========================================================
# REFRESH USER CACHE
# =========================================================

@shared_task
def refresh_users_cache():

    users = list(

        User.objects.values(

            'id',

            'username',

            'email',

            'phone_number',

            'role',

            'is_verified'
        )[:100]
    )

    cache.set(

        "users_cache",

        users,

        timeout=60 * 10
    )

    return "Users cache refreshed"