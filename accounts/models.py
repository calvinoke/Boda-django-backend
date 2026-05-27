from django.contrib.auth.models import AbstractUser
from django.db import models


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
    # EMAIL OPTIONAL
    # =====================================================

    # Used for:
    # - notifications
    # - password recovery
    # - communication
    # NOT login

    email = models.EmailField(

        unique=True,

        null=True,

        blank=True,

        db_index=True
    )

    # =====================================================
    # BASIC INFORMATION
    # =====================================================

    first_name = models.CharField(
        max_length=150
    )

    last_name = models.CharField(
        max_length=150
    )

    username = models.CharField(

        max_length=150,

        unique=True,

        db_index=True
    )

    # =====================================================
    # PHONE NUMBER
    # =====================================================

    # VALIDATION + NORMALIZATION
    # WILL BE HANDLED IN SERIALIZERS

    phone_number = models.CharField(

        max_length=15,

        unique=True,

        db_index=True
    )

    role = models.CharField(

        max_length=30,

        choices=ROLE_CHOICES,

        default='guest_rider',

        db_index=True
    )

    # =====================================================
    # ACCOUNT SECURITY
    # =====================================================

    is_verified = models.BooleanField(
        default=False
    )

    is_active = models.BooleanField(
        default=True
    )

    # =====================================================
    # TIMESTAMPS
    # =====================================================

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    # =====================================================
    # AUTHENTICATION
    # =====================================================

    USERNAME_FIELD = 'username'

    REQUIRED_FIELDS = ['phone_number']

    # =====================================================
    # MODEL METADATA
    # =====================================================

    class Meta:

        ordering = ['-created_at']

        indexes = [

            models.Index(fields=['username']),

            models.Index(fields=['phone_number']),

            models.Index(fields=['role']),

            models.Index(fields=['email']),
        ]

    # =====================================================
    # STRING REPRESENTATION
    # =====================================================

    def __str__(self):

        return (
            f"{self.username} - "
            f"{self.role}"
        )