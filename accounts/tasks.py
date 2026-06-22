import logging
from celery import shared_task
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import User

# Fix the import - import from email_utils, not utils
from .email_utils import send_welcome_email, send_otp_email, send_password_reset_email

logger = logging.getLogger("accounts.tasks")


@shared_task
def send_otp_task(phone: str, otp: str, purpose: str = 'verification'):
    """
    Send OTP via SMS and Email.
    
    Args:
        phone (str): Phone number to send OTP to
        otp (str): The OTP code
        purpose (str): Purpose of OTP (verification, password_reset, phone_change)
    
    Returns:
        bool: True if successful
    """
    try:
        # Send SMS (placeholder for SMS provider integration)
        logger.info(
            f"Sending OTP to {phone} for purpose: {purpose}",
            extra={
                "phone": phone,
                "purpose": purpose,
                "otp": otp  # Only log in development, remove in production
            }
        )
        
        # Print for development visibility
        print(f"📱 SMS OTP for {phone}: {otp} (purpose: {purpose})")
        
        # TODO: Integrate with SMS provider (Twilio, AfricasTalking, etc.)
        # Example with Twilio:
        # from twilio.rest import Client
        # client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        # message = client.messages.create(
        #     body=f"Your {purpose} OTP is: {otp}",
        #     from_=settings.TWILIO_PHONE_NUMBER,
        #     to=phone
        # )
        
        # Send Email (if user exists and has email)
        from .models import User
        try:
            user = User.objects.get(phone_number=phone)
            if user.email:
                send_otp_email(user, otp, purpose)
                logger.info(
                    f"OTP email sent to {user.email}",
                    extra={
                        "user_id": user.id,
                        "username": user.username,
                        "phone": phone,
                        "purpose": purpose
                    }
                )
        except User.DoesNotExist:
            logger.info(f"No user found for phone {phone}, skipping email")
        except Exception as e:
            logger.error(f"Failed to send OTP email: {e}")
            
        return True
        
    except Exception as e:
        logger.error(
            f"Failed to send OTP to {phone}: {str(e)}",
            extra={
                "phone": phone,
                "purpose": purpose,
                "error": str(e)
            }
        )
        raise


@shared_task
def send_welcome_email_task(user_id):
    """
    Send welcome email to new user.
    
    Args:
        user_id (int): ID of the user to send welcome email to
    
    Returns:
        bool: True if successful
    """
    try:
        from .models import User
        user = User.objects.get(id=user_id)
        
        if not user.email:
            logger.warning(
                f"User {user_id} has no email address, skipping welcome email",
                extra={"user_id": user_id, "username": user.username}
            )
            return False
        
        send_welcome_email(user)
        
        logger.info(
            f"Welcome email sent to user {user_id}",
            extra={
                "user_id": user_id,
                "username": user.username,
                "email": user.email
            }
        )
        return True
        
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found for welcome email")
        return False
    except Exception as e:
        logger.error(
            f"Failed to send welcome email to user {user_id}: {str(e)}",
            extra={"user_id": user_id, "error": str(e)}
        )
        raise


@shared_task
def broadcast_user_event(message: str):
    """
    Broadcast user events to websocket.
    
    Args:
        message (str): Message to broadcast
    
    Returns:
        bool: True if successful
    """
    try:
        logger.info(f"Broadcasting event: {message}")
        
        # TODO: Implement websocket broadcast
        # Example with Django Channels:
        # from channels.layers import get_channel_layer
        # from asgiref.sync import async_to_sync
        # channel_layer = get_channel_layer()
        # async_to_sync(channel_layer.group_send)(
        #     "users",
        #     {
        #         "type": "user_event",
        #         "message": message
        #     }
        # )
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to broadcast event: {str(e)}")
        return False


@shared_task
def refresh_users_cache():
    """
    Refresh user cache.
    Deletes the cached users list.
    
    Returns:
        bool: True if successful
    """
    try:
        cache.delete('users_list')
        logger.info("Users cache refreshed successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to refresh users cache: {str(e)}")
        return False


@shared_task
def send_password_reset_email_task(user_id, reset_token):
    """
    Send password reset email to user.
    
    Args:
        user_id (int): ID of the user
        reset_token (str): Password reset token
    
    Returns:
        bool: True if successful
    """
    try:
        from .models import User
        user = User.objects.get(id=user_id)
        
        if not user.email:
            logger.warning(
                f"User {user_id} has no email address, skipping password reset email",
                extra={"user_id": user_id, "username": user.username}
            )
            return False
        
        # Send password reset email using the email_utils function
        send_password_reset_email(user, reset_token)
        
        logger.info(
            f"Password reset email sent to user {user_id}",
            extra={
                "user_id": user_id,
                "username": user.username,
                "email": user.email
            }
        )
        return True
        
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found for password reset email")
        return False
    except Exception as e:
        logger.error(
            f"Failed to send password reset email: {str(e)}",
            extra={"user_id": user_id, "error": str(e)}
        )
        raise


@shared_task
def delete_expired_users():
    """
    Delete users that haven't been verified within a certain time.
    Scheduled task to clean up unverified users.
    
    Returns:
        int: Number of users deleted
    """
    try:
        # Delete users created more than 7 days ago that are not verified
        cutoff_date = timezone.now() - timedelta(days=7)
        
        expired_users = User.objects.filter(
            is_verified=False,
            is_active=True,
            created_at__lte=cutoff_date
        )
        
        count = expired_users.count()
        
        if count > 0:
            # Log before deletion
            for user in expired_users:
                logger.info(
                    f"Deleting expired unverified user: {user.username}",
                    extra={
                        "user_id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "created_at": user.created_at
                    }
                )
            
            # Delete users
            expired_users.delete()
            
            logger.info(f"Deleted {count} expired unverified users")
        
        return count
        
    except Exception as e:
        logger.error(f"Failed to delete expired users: {str(e)}")
        return 0