import logging

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator

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
        null=True,
        blank=True,
        db_index=True
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

    # =====================================================
    # TIMESTAMPS
    # =====================================================

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    # =====================================================
    # AUTH CONFIG
    # =====================================================

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['phone_number']

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
        ]
        swappable = 'AUTH_USER_MODEL'

    # =====================================================
    # SAVE HOOK (safe logging)
    # =====================================================

    def save(self, *args, **kwargs):

        # normalize username
        if self.username:
            self.username = self.username.strip()

        # normalize email
        if self.email:
            self.email = self.email.lower().strip()

        super().save(*args, **kwargs)

        logger.info(
            "User saved | id=%s | username=%s | role=%s",
            self.id,
            self.username,
            self.role
        )

    # =====================================================
    # STRING REPRESENTATION
    # =====================================================

    def __str__(self):
        return f"{self.username} - {self.role}"