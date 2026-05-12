from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator

User = settings.AUTH_USER_MODEL


# =========================================================
# PHONE VALIDATOR
# =========================================================

phone_validator = RegexValidator(
    regex=r'^\+256[0-9]{9}$',
    message='Phone number must be in format: +2567XXXXXXXX'
)


# =========================================================
# STAGE MODEL
# =========================================================

class Stage(models.Model):

    # =====================================================
    # BASIC INFORMATION
    # =====================================================

    name = models.CharField(
        max_length=255,
        unique=True,
        db_index=True
    )

    district = models.CharField(
        max_length=255,
        db_index=True
    )

    division = models.CharField(
        max_length=255,
        db_index=True
    )

    parish = models.CharField(
        max_length=255,
        db_index=True
    )

    village = models.CharField(
        max_length=255,
        db_index=True
    )

    # =====================================================
    # STAGE LEADERSHIP USERS
    # =====================================================

    chairman = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='chairman_stages',
        limit_choices_to={
            'role': 'stage_chairman'
        }
    )

    secretary = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='secretary_stages',
        limit_choices_to={
            'role': 'stage_secretary'
        }
    )

    defense = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='defense_stages',
        limit_choices_to={
            'role': 'stage_defense'
        }
    )

    # =====================================================
    # CONTACT BACKUP (OPTIONAL)
    # =====================================================

    chairman_phone = models.CharField(
        max_length=15,
        validators=[phone_validator]
    )

    secretary_phone = models.CharField(
        max_length=15,
        validators=[phone_validator]
    )

    defense_phone = models.CharField(
        max_length=15,
        validators=[phone_validator]
    )

    # =====================================================
    # GPS LOCATION
    # =====================================================

    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        db_index=True
    )

    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        db_index=True
    )

    # =====================================================
    # STATUS
    # =====================================================

    is_active = models.BooleanField(
        default=True,
        db_index=True
    )

    # =====================================================
    # SECURITY ANALYTICS
    # =====================================================

    total_registered_riders = models.PositiveIntegerField(
        default=0
    )

    total_guest_riders_seen = models.PositiveIntegerField(
        default=0
    )

    suspicious_activity_score = models.IntegerField(
        default=0
    )

    # =====================================================
    # TIMESTAMPS
    # =====================================================

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    # =====================================================
    # META
    # =====================================================

    class Meta:

        ordering = ['name']

        indexes = [

            models.Index(fields=['name']),

            models.Index(fields=['district']),

            models.Index(fields=['division']),

            models.Index(fields=['parish']),

            models.Index(fields=['village']),

            models.Index(fields=['is_active']),

            models.Index(fields=['latitude', 'longitude']),
        ]

    # =====================================================
    # STRING
    # =====================================================

    def __str__(self):

        return self.name