import secrets
import hashlib
import logging
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger("accounts.utils")

def generate_otp():
    return str(secrets.randbelow(900000) + 100000)

def hash_otp(otp: str) -> str:
    return hashlib.sha256(otp.encode()).hexdigest()

def verify_otp(otp: str, hashed: str) -> bool:
    return hash_otp(otp) == hashed

def store_otp(phone: str, otp: str, purpose: str = 'verification'):
    key = f"otp:{purpose}:{phone}"
    cache.set(key, hash_otp(otp), timeout=300)
    logger.debug(f"OTP stored for {phone} with purpose {purpose}")
    return True

def verify_otp_code(phone: str, otp: str, purpose: str = 'verification') -> bool:
    key = f"otp:{purpose}:{phone}"
    cached_otp = cache.get(key)
    
    if not cached_otp:
        logger.warning(f"No OTP found for {phone} with purpose {purpose}")
        return False
    
    if verify_otp(otp, cached_otp):
        cache.delete(key)
        logger.info(f"OTP verified for {phone} with purpose {purpose}")
        return True
    
    logger.warning(f"Invalid OTP for {phone} with purpose {purpose}")
    return False

def rate_limited(key: str, limit: int = 5, window: int = 300) -> bool:
    attempts_key = f"otp_attempts:{key}"
    attempts = cache.get(attempts_key, 0)
    
    if attempts >= limit:
        logger.warning(f"Rate limit exceeded for {key}")
        return True
    
    cache.set(attempts_key, attempts + 1, timeout=window)
    return False

def reset_rate_limit(key: str):
    cache.delete(f"otp_attempts:{key}")
    logger.debug(f"Rate limit reset for {key}")

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def get_user_agent(request):
    return request.META.get('HTTP_USER_AGENT', '')