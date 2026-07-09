import logging
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator, EmailValidator
from django.utils import timezone
from django.conf import settings

logger = logging.getLogger("accounts.models")

# =========================================================
# PHONE VALIDATOR (production-safe)
# =========================================================

phone_validator = RegexValidator(
    regex=r'^\+256[0-9]{9}$',
    message='Phone number must be in format: +2567XXXXXXXX'
)

# =========================================================
# CUSTOM USER MODEL
# =========================================================

class User(AbstractUser):
    ROLE_CHOICES = (
        ('super_admin', 'Super Admin'),
        ('stage_chairman', 'Stage Chairman'),
        ('stage_secretary', 'Stage Secretary'),
        ('stage_defense', 'Stage Defense'),
        ('rider', 'Rider'),
        ('guest_rider', 'Guest Rider'),
    )

    # =====================================================
    # CORE IDENTITY
    # =====================================================

    email = models.EmailField(
        unique=True,
        db_index=True,
        null=True,
        blank=True,
        validators=[EmailValidator()]
    )

    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)

    username = models.CharField(
        max_length=150,
        unique=True,
        db_index=True
    )

    phone_number = models.CharField(
        max_length=15,
        unique=True,
        db_index=True,
        validators=[phone_validator]
    )

    role = models.CharField(
        max_length=30,
        choices=ROLE_CHOICES,
        default='guest_rider',
        db_index=True
    )

    # =====================================================
    # SECURITY FLAGS
    # =====================================================

    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_phone_verified = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    
    # Account lockout
    failed_login_attempts = models.IntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)

    # =====================================================
    # 2FA
    # =====================================================
    totp_secret = models.CharField(max_length=255, null=True, blank=True)
    is_2fa_enabled = models.BooleanField(default=False)

    # =====================================================
    # TIMESTAMPS
    # =====================================================

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    last_login_device = models.CharField(max_length=255, null=True, blank=True)

    # =====================================================
    # AUTH CONFIG - EMAIL IS NOW REQUIRED FOR SUPERUSER
    # =====================================================

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['phone_number', 'email']  # ← ADDED EMAIL HERE

    # =====================================================
    # META
    # =====================================================

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['username']),
            models.Index(fields=['phone_number']),
            models.Index(fields=['role']),
            models.Index(fields=['email']),
            models.Index(fields=['is_verified']),
            models.Index(fields=['is_active']),
        ]
        swappable = 'AUTH_USER_MODEL'

    # =====================================================
    # SAVE HOOK (safe logging) - FIXED FOR EMPTY EMAIL
    # =====================================================

    def save(self, *args, **kwargs):
        # Normalize username
        if self.username:
            self.username = self.username.strip()

        # Normalize email - convert empty string to None to avoid unique constraint issues
        if self.email == '':
            self.email = None
        elif self.email:
            self.email = self.email.lower().strip()

        # Ensure phone number is set
        if not self.phone_number:
            logger.warning(f"User {self.username} has no phone number")

        super().save(*args, **kwargs)

        logger.info(
            "User saved | id=%s | username=%s | role=%s | email=%s",
            self.id,
            self.username,
            self.role,
            self.email
        )

    # =====================================================
    # STRING REPRESENTATION
    # =====================================================

    def __str__(self):
        return f"{self.username} - {self.role}"
    
    # =====================================================
    # LOCKOUT METHODS
    # =====================================================
    
    def is_locked(self):
        if self.locked_until and timezone.now() < self.locked_until:
            return True
        return False
    
    def lock_account(self, duration_minutes=15):
        self.locked_until = timezone.now() + timezone.timedelta(minutes=duration_minutes)
        self.save(update_fields=['locked_until'])
        logger.warning(f"Account locked: {self.username} until {self.locked_until}")
    
    def reset_failed_attempts(self):
        self.failed_login_attempts = 0
        self.locked_until = None
        self.save(update_fields=['failed_login_attempts', 'locked_until'])

# =========================================================
# SYSTEM LOG
# =========================================================

class SystemLog(models.Model):
    ACTION_TYPES = (
        ("OTP_VERIFIED", "OTP_VERIFIED"),
        ("PASSWORD_RESET", "PASSWORD_RESET"),
        ("USER_CREATED", "USER_CREATED"),
        ("LOGIN", "LOGIN"),
        ("LOGIN_FAILED", "LOGIN_FAILED"),
        ("LOGOUT", "LOGOUT"),
        ("ACCOUNT_LOCKED", "ACCOUNT_LOCKED"),
        ("PASSWORD_CHANGED", "PASSWORD_CHANGED"),
        ("ROLE_CHANGED", "ROLE_CHANGED"),
        ("PHONE_CHANGED", "PHONE_CHANGED"),
        ("EMAIL_CHANGED", "EMAIL_CHANGED"),
        ("2FA_ENABLED", "2FA_ENABLED"),
        ("2FA_DISABLED", "2FA_DISABLED"),
        ("OTHER", "OTHER"),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="system_logs",
        db_index=True
    )

    action = models.CharField(max_length=50, choices=ACTION_TYPES, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["action"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["user", "action"]),
        ]

    def __str__(self):
        return f"{self.action} - {self.created_at}"

# =========================================================
# PASSWORD RESET TOKEN
# =========================================================

class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reset_tokens')
    token = models.CharField(max_length=255, unique=True, db_index=True)
    phone_number = models.CharField(max_length=15)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['phone_number']),
            models.Index(fields=['expires_at']),
        ]
    
    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at
    
    def __str__(self):
        return f"Reset token for {self.user.username}"

# =========================================================
# LOGIN ATTEMPT
# =========================================================

class LoginAttempt(models.Model):
    phone_number = models.CharField(max_length=15, db_index=True)
    ip_address = models.GenericIPAddressField()
    success = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['phone_number', 'timestamp']),
            models.Index(fields=['ip_address', 'timestamp']),
        ]