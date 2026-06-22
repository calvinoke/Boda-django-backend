import secrets
import hashlib
import logging
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger("accounts.utils")


# =========================================================
# OTP GENERATION & HASHING
# =========================================================

def generate_otp():
    """
    Generate a 6-digit OTP code.
    
    Returns:
        str: 6-digit OTP code
    """
    return str(secrets.randbelow(900000) + 100000)


def hash_otp(otp: str) -> str:
    """
    Hash an OTP code using SHA-256.
    
    Args:
        otp (str): OTP code to hash
    
    Returns:
        str: Hashed OTP
    """
    return hashlib.sha256(otp.encode()).hexdigest()


def verify_otp(otp: str, hashed: str) -> bool:
    """
    Verify an OTP against its hash.
    
    Args:
        otp (str): OTP to verify
        hashed (str): Hashed OTP to compare against
    
    Returns:
        bool: True if OTP matches hash
    """
    return hash_otp(otp) == hashed


# =========================================================
# OTP STORAGE & VERIFICATION
# =========================================================

def store_otp(phone: str, otp: str, purpose: str = 'verification'):
    """
    Store OTP in cache with purpose and expiration.
    
    Args:
        phone (str): Phone number
        otp (str): OTP code
        purpose (str): Purpose of OTP (verification, password_reset, phone_change)
    
    Returns:
        bool: True if stored successfully
    """
    try:
        key = f"otp:{purpose}:{phone}"
        cache.set(key, hash_otp(otp), timeout=300)  # 5 minutes expiration
        
        logger.debug(
            f"OTP stored for {phone} with purpose {purpose}",
            extra={
                "phone": phone,
                "purpose": purpose,
                "expires_in": "300 seconds"
            }
        )
        return True
    except Exception as e:
        logger.error(f"Failed to store OTP for {phone}: {str(e)}")
        return False


def verify_otp_code(phone: str, otp: str, purpose: str = 'verification') -> bool:
    """
    Verify an OTP code against stored hash.
    
    Args:
        phone (str): Phone number
        otp (str): OTP to verify
        purpose (str): Purpose of OTP
    
    Returns:
        bool: True if OTP is valid
    """
    try:
        key = f"otp:{purpose}:{phone}"
        cached_otp = cache.get(key)
        
        if not cached_otp:
            logger.warning(
                f"No OTP found for {phone} with purpose {purpose}",
                extra={
                    "phone": phone,
                    "purpose": purpose
                }
            )
            return False
        
        if verify_otp(otp, cached_otp):
            # Delete OTP after successful verification
            cache.delete(key)
            logger.info(
                f"OTP verified for {phone} with purpose {purpose}",
                extra={
                    "phone": phone,
                    "purpose": purpose
                }
            )
            return True
        
        logger.warning(
            f"Invalid OTP for {phone} with purpose {purpose}",
            extra={
                "phone": phone,
                "purpose": purpose
            }
        )
        return False
        
    except Exception as e:
        logger.error(
            f"Error verifying OTP for {phone}: {str(e)}",
            extra={
                "phone": phone,
                "purpose": purpose,
                "error": str(e)
            }
        )
        return False


# =========================================================
# RATE LIMITING
# =========================================================

def rate_limited(key: str, limit: int = 5, window: int = 300) -> bool:
    """
    Check if rate limit has been exceeded for a key.
    
    Args:
        key (str): Key to check (phone or IP)
        limit (int): Maximum attempts allowed
        window (int): Time window in seconds
    
    Returns:
        bool: True if rate limit exceeded
    """
    try:
        attempts_key = f"otp_attempts:{key}"
        attempts = cache.get(attempts_key, 0)
        
        if attempts >= limit:
            logger.warning(
                f"Rate limit exceeded for {key}",
                extra={
                    "key": key,
                    "limit": limit,
                    "attempts": attempts,
                    "window": window
                }
            )
            return True
        
        cache.set(attempts_key, attempts + 1, timeout=window)
        logger.debug(
            f"Rate limit check for {key}: {attempts + 1}/{limit}",
            extra={
                "key": key,
                "attempts": attempts + 1,
                "limit": limit
            }
        )
        return False
        
    except Exception as e:
        logger.error(f"Rate limit check failed for {key}: {str(e)}")
        return False  # Allow on error to not block users


def reset_rate_limit(key: str):
    """
    Reset rate limit for a key.
    
    Args:
        key (str): Key to reset (phone or IP)
    """
    try:
        cache.delete(f"otp_attempts:{key}")
        logger.debug(
            f"Rate limit reset for {key}",
            extra={"key": key}
        )
    except Exception as e:
        logger.error(f"Failed to reset rate limit for {key}: {str(e)}")


# =========================================================
# REQUEST HELPERS
# =========================================================

def get_client_ip(request):
    """
    Get client IP address from request.
    
    Args:
        request: Django request object
    
    Returns:
        str: Client IP address
    """
    try:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # Get the first IP in the forwarded chain
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        
        logger.debug(f"Client IP: {ip}")
        return ip
        
    except Exception as e:
        logger.error(f"Failed to get client IP: {str(e)}")
        return '0.0.0.0'  # Default fallback


def get_user_agent(request):
    """
    Get user agent from request.
    
    Args:
        request: Django request object
    
    Returns:
        str: User agent string
    """
    try:
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        return user_agent[:255]  # Truncate to prevent large strings
        
    except Exception as e:
        logger.error(f"Failed to get user agent: {str(e)}")
        return ''


# =========================================================
# OTP CLEANUP
# =========================================================

def cleanup_expired_otps(age_minutes: int = 10):
    """
    Clean up expired OTPs from cache.
    Note: This is mostly handled automatically by cache expiration.
    
    Args:
        age_minutes (int): Age in minutes to consider expired
    
    Returns:
        int: Number of OTPs cleaned up
    """
    try:
        # Since we use cache with timeout, this is handled automatically
        # This function can be used for manual cleanup if needed
        logger.info(f"OTP cleanup completed (automatic cache expiration)")
        return 0
        
    except Exception as e:
        logger.error(f"OTP cleanup failed: {str(e)}")
        return 0


# =========================================================
# TOKEN GENERATION
# =========================================================

def generate_secure_token(length: int = 32) -> str:
    """
    Generate a secure random token.
    
    Args:
        length (int): Length of token
    
    Returns:
        str: Secure random token
    """
    import base64
    token_bytes = secrets.token_bytes(length)
    token = base64.urlsafe_b64encode(token_bytes).decode('utf-8')
    logger.debug(f"Generated secure token of length {len(token)}")
    return token


# =========================================================
# PHONE HELPERS
# =========================================================

def mask_phone(phone: str) -> str:
    """
    Mask phone number for display (e.g., +2567XXXXXX78).
    
    Args:
        phone (str): Full phone number
    
    Returns:
        str: Masked phone number
    """
    if not phone:
        return ''
    
    if len(phone) <= 6:
        return phone
    
    # Keep first 4 and last 2 digits
    masked = phone[:4] + 'XXXXXX' + phone[-2:]
    return masked


def mask_email(email: str) -> str:
    """
    Mask email for display (e.g., j***@example.com).
    
    Args:
        email (str): Full email address
    
    Returns:
        str: Masked email
    """
    if not email or '@' not in email:
        return ''
    
    local, domain = email.split('@', 1)
    if len(local) <= 2:
        masked_local = local[0] + '***'
    else:
        masked_local = local[:1] + '***' + local[-1:]
    
    return f"{masked_local}@{domain}"


# =========================================================
# TIME HELPERS
# =========================================================

def get_otp_expiry_timestamp(created_at=None, expiry_seconds: int = 300):
    """
    Get expiry timestamp for OTP.
    
    Args:
        created_at: Creation time (defaults to now)
        expiry_seconds: Expiry in seconds
    
    Returns:
        datetime: Expiry time
    """
    if created_at is None:
        created_at = timezone.now()
    return created_at + timedelta(seconds=expiry_seconds)


def is_otp_expired(created_at, expiry_seconds: int = 300) -> bool:
    """
    Check if OTP has expired.
    
    Args:
        created_at: Creation time
        expiry_seconds: Expiry in seconds
    
    Returns:
        bool: True if expired
    """
    if created_at is None:
        return True
    expiry_time = created_at + timedelta(seconds=expiry_seconds)
    return timezone.now() > expiry_time