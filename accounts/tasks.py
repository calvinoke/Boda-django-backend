import logging

from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.core.cache import cache

from .models import User
from .serializers import DynamicUserSerializer


logger = logging.getLogger("accounts.tasks")


# =========================================================
# BROADCAST USER EVENT (REAL-TIME via WebSockets)
# =========================================================

@shared_task(bind=True, max_retries=3)
def broadcast_user_event(self, message):
    try:
        channel_layer = get_channel_layer()

        async_to_sync(channel_layer.group_send)(
            "accounts",
            {
                "type": "send_user_notification",
                "event_type": "user_event",
                "message": message,
            }
        )

        logger.info(
            "User event broadcast successful | event=%s",
            str(message)[:200]
        )

        return "Event broadcast sent"

    except Exception as exc:
        logger.exception(
            "Failed to broadcast user event | message=%s | error=%s",
            message,
            str(exc)
        )

        raise self.retry(exc=exc, countdown=5)


# =========================================================
# REFRESH USER CACHE (REDIS + SERIALIZER SAFE)
# =========================================================

@shared_task
def refresh_users_cache():
    try:
        users = (
            User.objects.all()
            .order_by("-created_at")[:100]
        )

        serialized_users = DynamicUserSerializer(
            users,
            many=True
        ).data

        cache.set(
            "users_cache",
            serialized_users,
            timeout=60 * 10  # 10 minutes
        )

        logger.info("Users cache refreshed | count=%s", len(serialized_users))

        return "Users cache refreshed successfully"

    except Exception as exc:
        logger.exception("Failed to refresh users cache | error=%s", str(exc))
        return "Cache refresh failed"


# =========================================================
# FUTURE READY: OTP TASK PLACEHOLDER
# =========================================================

@shared_task(bind=True, max_retries=3)
def send_otp_task(self, phone_number, otp_code):
    try:
        logger.info(
            "OTP send requested | phone=%s",
            phone_number
        )

        # TODO: integrate SMS provider (Twilio / Africa's Talking)
        # sms_provider.send(phone_number, otp_code)

        return f"OTP sent to {phone_number}"

    except Exception as exc:
        logger.exception(
            "OTP send failed | phone=%s | error=%s",
            phone_number,
            str(exc)
        )

        raise self.retry(exc=exc, countdown=10)


# =========================================================
# FUTURE READY: OTP EXPIRY CLEANUP
# =========================================================

@shared_task
def cleanup_expired_otps():
    try:
        # Example future Redis cleanup logic placeholder
        logger.info("OTP cleanup executed")

        return "Expired OTP cleanup completed"

    except Exception as exc:
        logger.exception("OTP cleanup failed | error=%s", str(exc))
        return "OTP cleanup failed"