from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.core.cache import cache
from .models import User
from .serializers import DynamicUserSerializer


# =========================================================
# BROADCAST USER EVENT (REAL-TIME via WebSockets)
# =========================================================

@shared_task
def broadcast_user_event(message):

    channel_layer = get_channel_layer()

    async_to_sync(channel_layer.group_send)(
        "accounts",
        {
            "type": "send_user_notification",
            "event_type": "user_event",
            "message": message,
        }
    )

    return "Event broadcast sent"


# =========================================================
# REFRESH USER CACHE (REDIS + SERIALIZER SAFE)
# =========================================================

@shared_task
def refresh_users_cache():

    users = User.objects.all().order_by(
        '-created_at'
    )[:100]

    serialized_users = DynamicUserSerializer(
        users,
        many=True
    ).data

    cache.set(
        "users_cache",
        serialized_users,
        timeout=60 * 10  # 10 minutes
    )

    return "Users cache refreshed successfully"


# =========================================================
# FUTURE READY: OTP TASK PLACEHOLDER (EXTENSION POINT)
# =========================================================

@shared_task
def send_otp_task(phone_number, otp_code):

    """
    This is a placeholder for:
    - SMS OTP sending (Africa's Talking / Twilio)
    - Redis OTP storage
    - rate limiting
    """

    # Example integration point:
    # sms_provider.send(phone_number, otp_code)

    return f"OTP sent to {phone_number}"


# =========================================================
# FUTURE READY: OTP EXPIRY CLEANUP
# =========================================================

@shared_task
def cleanup_expired_otps():

    """
    This will later:
    - remove expired OTP keys from Redis
    - prevent OTP reuse
    """

    return "Expired OTP cleanup completed"