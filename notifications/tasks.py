from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.core.cache import cache
from .models import Notification


# =========================================================
# CREATE NOTIFICATION
# =========================================================

@shared_task
def create_notification(

    user_id,

    title,

    message,

    notification_type='general'
):

    from accounts.models import User

    try:

        user = User.objects.get(id=user_id)

        notification = Notification.objects.create(

            user=user,

            title=title,

            message=message,

            notification_type=notification_type
        )

        # =================================================
        # REFRESH CACHE
        # =================================================

        refresh_notifications_cache(user.id)

        # =================================================
        # SEND REALTIME WEBSOCKET EVENT
        # =================================================

        channel_layer = get_channel_layer()

        async_to_sync(
            channel_layer.group_send
        )(
            f"notifications_{user.id}",

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

        return f"Notification sent to {user.username}"

    except User.DoesNotExist:

        return "User not found"


# =========================================================
# CACHE USER NOTIFICATIONS
# =========================================================

@shared_task
def refresh_notifications_cache(user_id):

    notifications = list(

        Notification.objects.filter(
            user_id=user_id
        ).values(
            'id',
            'title',
            'message',
            'notification_type',
            'is_read',
            'created_at'
        )[:100]
    )

    cache.set(

        f"user_notifications_{user_id}",

        notifications,

        timeout=60 * 10
    )

    return "Notification cache refreshed"