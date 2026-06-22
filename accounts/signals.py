import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.utils import timezone  # ← Add this import
from django.core.cache import cache  # ← Also import cache at top
from .models import User, SystemLog

# Set up logger
logger = logging.getLogger("accounts.signals")

@receiver(post_save, sender=User)
def auto_promote_first_user(sender, instance, created, **kwargs):
    """
    Auto-promote the first user to super_admin.
    This ensures there's always at least one super admin in the system.
    """
    if created and User.objects.count() == 1:
        old_role = instance.role
        
        # Promote to super_admin
        instance.role = 'super_admin'
        instance.is_verified = True
        instance.is_phone_verified = True
        instance.is_email_verified = True
        instance.is_staff = True
        instance.is_superuser = True
        instance.save()
        
        # Log the promotion in SystemLog
        SystemLog.objects.create(
            user=instance,
            action="ROLE_CHANGED",
            metadata={
                "old_role": old_role,
                "new_role": "super_admin",
                "reason": "First user auto-promotion"
            }
        )
        
        # Log with structured logging
        logger.info(
            "First user auto-promoted to super_admin",
            extra={
                "user_id": instance.id,
                "username": instance.username,
                "old_role": old_role,
                "new_role": "super_admin",
                "reason": "first_user_auto_promotion"
            }
        )
        
        # Also print for development visibility
        print(f"✅ First user '{instance.username}' automatically promoted to super_admin")

@receiver(post_save, sender=User)
def log_user_creation(sender, instance, created, **kwargs):
    """
    Log user creation events.
    Creates a SystemLog entry whenever a new user is registered.
    """
    if created:
        # Create SystemLog entry
        SystemLog.objects.create(
            user=instance,
            action="USER_CREATED",
            metadata={
                "username": instance.username,
                "role": instance.role,
                "email": instance.email,
                "phone_number": instance.phone_number
            }
        )
        
        # Log with structured logging
        logger.info(
            "New user created",
            extra={
                "user_id": instance.id,
                "username": instance.username,
                "role": instance.role,
                "email": instance.email,
                "phone_number": instance.phone_number
            }
        )

@receiver(post_save, sender=User)
def log_user_update(sender, instance, created, **kwargs):
    """
    Log user updates (role changes, verification status, etc.)
    This is a backup in case the view doesn't capture all changes.
    """
    if not created:
        # Check if any important fields changed
        try:
            # Get the previous state from the database
            old_instance = User.objects.get(id=instance.id)
            
            changes = {}
            
            # Check for role changes
            if old_instance.role != instance.role:
                changes['role'] = {
                    'old': old_instance.role,
                    'new': instance.role
                }
            
            # Check for verification changes
            if old_instance.is_verified != instance.is_verified:
                changes['is_verified'] = {
                    'old': old_instance.is_verified,
                    'new': instance.is_verified
                }
            
            # Check for active status changes
            if old_instance.is_active != instance.is_active:
                changes['is_active'] = {
                    'old': old_instance.is_active,
                    'new': instance.is_active
                }
            
            # Check for phone verification changes
            if old_instance.is_phone_verified != instance.is_phone_verified:
                changes['is_phone_verified'] = {
                    'old': old_instance.is_phone_verified,
                    'new': instance.is_phone_verified
                }
            
            # Check for email verification changes
            if old_instance.is_email_verified != instance.is_email_verified:
                changes['is_email_verified'] = {
                    'old': old_instance.is_email_verified,
                    'new': instance.is_email_verified
                }
            
            # If there were changes, log them
            if changes:
                # Only log if not already logged by the view
                # We'll check if a recent SystemLog entry exists for this user
                recent_logs = SystemLog.objects.filter(
                    user=instance,
                    action__in=['ROLE_CHANGED', 'PASSWORD_CHANGED'],
                    created_at__gte=timezone.now() - timezone.timedelta(seconds=10)
                )
                
                if not recent_logs.exists():
                    SystemLog.objects.create(
                        user=instance,
                        action="OTHER",
                        metadata={
                            "changes": changes,
                            "trigger": "signal_post_save"
                        }
                    )
                    
                    logger.info(
                        "User updated (via signal)",
                        extra={
                            "user_id": instance.id,
                            "username": instance.username,
                            "changes": changes
                        }
                    )
                    
        except User.DoesNotExist:
            # This is a new user, handled by the creation signal
            pass
        except Exception as e:
            logger.error(
                f"Error in log_user_update signal: {str(e)}",
                extra={
                    "user_id": instance.id,
                    "username": instance.username,
                    "error": str(e)
                }
            )

@receiver(post_save, sender=User)
def send_welcome_email(sender, instance, created, **kwargs):
    """
    Send welcome email to new users (placeholder for future implementation)
    """
    if created:
        # Placeholder for email sending logic
        # This can be implemented later with Celery tasks
        logger.info(
            f"Welcome email would be sent to {instance.email} (not implemented yet)",
            extra={
                "user_id": instance.id,
                "username": instance.username,
                "email": instance.email
            }
        )
        
        # TODO: Implement actual email sending
        # from .tasks import send_welcome_email_task
        # send_welcome_email_task.delay(instance.id)

@receiver(post_save, sender=User)
def update_user_cache(sender, instance, created, **kwargs):
    """
    Invalidate user cache when user is updated
    """
    # Invalidate the user cache
    cache.delete(f"user_{instance.id}")
    cache.delete("users_list")
    cache.delete(f"user_{instance.username}")
    
    if created:
        logger.debug(f"Cache invalidated for new user: {instance.username}")
    else:
        logger.debug(f"Cache invalidated for updated user: {instance.username}")