from celery import shared_task
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import (
    Announcement,
    Condolence
)

from .services import (
    cache_latest_announcements,
    cache_latest_condolences
)


# =========================================================
# BROADCAST ANNOUNCEMENT
# =========================================================

@shared_task
def broadcast_announcement_task(
    announcement_id
):

    try:

        announcement = Announcement.objects.get(
            id=announcement_id
        )

        channel_layer = get_channel_layer()

        async_to_sync(
            channel_layer.group_send
        )(

            "announcements",

            {

                "type": "send_announcement",

                "message": {

                    "id": announcement.id,

                    "title": announcement.title,

                    "message": announcement.message,

                    "announcement_type":
                        announcement.announcement_type,
                }
            }
        )

    except Announcement.DoesNotExist:
        pass


# =========================================================
# BROADCAST CONDOLENCE
# =========================================================

@shared_task
def broadcast_condolence_task(
    condolence_id
):

    try:

        condolence = Condolence.objects.get(
            id=condolence_id
        )

        channel_layer = get_channel_layer()

        async_to_sync(
            channel_layer.group_send
        )(

            "condolences",

            {

                "type": "send_condolence",

                "message": {

                    "id": condolence.id,

                    "description":
                        condolence.description,

                    "burial_location":
                        condolence.burial_location,

                    "status":
                        condolence.status,
                }
            }
        )

    except Condolence.DoesNotExist:
        pass


# =========================================================
# REFRESH REDIS CACHE
# =========================================================

@shared_task
def refresh_announcements_cache():

    cache_latest_announcements()

    cache_latest_condolences()