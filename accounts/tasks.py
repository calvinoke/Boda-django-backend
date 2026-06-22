import logging
from celery import shared_task
from django.core.cache import cache

logger = logging.getLogger("accounts.tasks")

@shared_task
def send_otp_task(phone: str, otp: str, purpose: str = 'verification'):
    try:
        logger.info(f"Sending OTP {otp} to {phone} for purpose: {purpose}")
        # TODO: Integrate with SMS provider (Twilio, AfricasTalking, etc.)
        print(f"📱 OTP for {phone}: {otp} (purpose: {purpose})")
        return True
    except Exception as e:
        logger.error(f"Failed to send OTP to {phone}: {e}")
        raise

@shared_task
def broadcast_user_event(message: str):
    logger.info(f"Broadcasting: {message}")
    return True

@shared_task
def refresh_users_cache():
    cache.delete('users_list')
    logger.info("Users cache refreshed")
    return True