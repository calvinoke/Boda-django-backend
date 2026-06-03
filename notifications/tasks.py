import logging
from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.core.cache import cache
from .models import Notification
from accounts.models import User

logger = logging.getLogger("notifications.tasks")


# =========================================================
# CREATE NOTIFICATION
# =========================================================

@shared_task
def create_notification(
    user_id,
    title,
    message,
    notification_type="general"
):

    try:

        user = User.objects.get(id=user_id)

        notification = Notification.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type
        )

        logger.info(
            f"Notification created | notification_id={notification.id} | user_id={user_id}"
        )

        # =================================================
        # CACHE REFRESH
        # =================================================

        try:
            refresh_notifications_cache.delay(user_id)
        except Exception as exc:
            logger.error(
                f"Cache refresh task failed | user_id={user_id} | error={str(exc)}"
            )

        # =================================================
        # REALTIME WEBSOCKET PUSH
        # =================================================

        try:
            channel_layer = get_channel_layer()

            async_to_sync(channel_layer.group_send)(
                f"notifications_{user_id}",
                {
                    "type": "send_notification",
                    "data": {
                        "id": notification.id,
                        "title": notification.title,
                        "message": notification.message,
                        "notification_type": notification.notification_type,
                        "is_read": notification.is_read,
                        "created_at": str(notification.created_at),
                    }
                }
            )

            logger.info(
                f"Notification broadcasted | notification_id={notification.id} | user_id={user_id}"
            )

        except Exception as exc:
            logger.error(
                f"WebSocket broadcast failed | notification_id={notification.id} | error={str(exc)}"
            )

        return f"Notification sent to {user.username}"

    except User.DoesNotExist:
        logger.warning(f"Notification failed: user not found | user_id={user_id}")
        return "User not found"

    except Exception as exc:
        logger.error(
            f"Notification creation failed | user_id={user_id} | error={str(exc)}"
        )
        raise


# =========================================================
# CACHE USER NOTIFICATIONS
# =========================================================

@shared_task
def refresh_notifications_cache(user_id):

    try:

        notifications = list(
            Notification.objects.filter(user_id=user_id).values(
                "id",
                "title",
                "message",
                "notification_type",
                "is_read",
                "created_at"
            )[:100]
        )

        cache.set(
            f"user_notifications_{user_id}",
            notifications,
            timeout=60 * 10
        )

        logger.info(
            f"Notification cache refreshed | user_id={user_id} | count={len(notifications)}"
        )

        return "Notification cache refreshed"

    except Exception as exc:
        logger.error(
            f"Cache refresh failed | user_id={user_id} | error={str(exc)}"
        )
        raise