import logging
from celery import shared_task
from celery.exceptions import Retry
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import DatabaseError
from .models import Announcement, Condolence
from .services import (cache_latest_announcements,cache_latest_condolences)

logger = logging.getLogger("celery")


# =========================================================
# ANNOUNCEMENT BROADCAST
# =========================================================

@shared_task(bind=True, max_retries=3)
def broadcast_announcement_task(self, announcement_id):

    try:
        announcement = Announcement.objects.get(id=announcement_id)

        channel_layer = get_channel_layer()

        async_to_sync(channel_layer.group_send)(
            "announcements",
            {
                "type": "send_announcement",
                "message": {
                    "id": announcement.id,
                    "title": announcement.title,
                    "message": announcement.message,
                    "announcement_type": announcement.announcement_type,
                },
            },
        )

        logger.info(f"Announcement broadcasted | id={announcement_id}")

    except Announcement.DoesNotExist:
        logger.warning(f"Announcement not found | id={announcement_id}")

    except Exception as exc:
        logger.error(
            f"Announcement broadcast failed | id={announcement_id} | error={str(exc)}"
        )

        raise self.retry(exc=exc, countdown=5)


# =========================================================
# CONDOLENCE BROADCAST
# =========================================================

@shared_task(bind=True, max_retries=3)
def broadcast_condolence_task(self, condolence_id):

    try:
        condolence = Condolence.objects.get(id=condolence_id)

        channel_layer = get_channel_layer()

        async_to_sync(channel_layer.group_send)(
            "condolences",
            {
                "type": "send_condolence",
                "message": {
                    "id": condolence.id,
                    "description": condolence.description,
                    "burial_location": condolence.burial_location,
                    "status": condolence.status,
                },
            },
        )

        logger.info(f"Condolence broadcasted | id={condolence_id}")

    except Condolence.DoesNotExist:
        logger.warning(f"Condolence not found | id={condolence_id}")

    except Exception as exc:
        logger.error(
            f"Condolence broadcast failed | id={condolence_id} | error={str(exc)}"
        )

        raise self.retry(exc=exc, countdown=5)


# =========================================================
# CACHE REFRESH (ISOLATED SAFE EXECUTION)
# =========================================================

@shared_task
def refresh_announcements_cache():

    try:
        cache_latest_announcements()
        logger.info("Announcements cache refreshed")

    except Exception as exc:
        logger.error(f"Announcements cache refresh failed: {str(exc)}")


@shared_task
def refresh_condolences_cache():

    try:
        cache_latest_condolences()
        logger.info("Condolences cache refreshed")

    except Exception as exc:
        logger.error(f"Condolences cache refresh failed: {str(exc)}")