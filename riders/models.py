from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator

User = settings.AUTH_USER_MODEL


# =========================================================
# VALIDATORS
# =========================================================

phone_validator = RegexValidator(
    regex=r'^\+256[0-9]{9}$',
    message='Phone number must be in format: +2567XXXXXXXX'
)

plate_validator = RegexValidator(
    regex=r'^[A-Z0-9]+$',
    message='Plate must contain uppercase letters and numbers only'
)


# =========================================================
# REGISTERED STAGE RIDERS
# =========================================================

class RiderProfile(models.Model):

    STATUS_CHOICES = (

        ('pending', 'Pending'),

        ('approved', 'Approved'),

        ('rejected', 'Rejected'),

        ('suspended', 'Suspended'),
    )

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='rider_profile'
    )

    stage = models.ForeignKey(
        'stages.Stage',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='riders'
    )

    # =====================================================
    # IDENTITY
    # =====================================================

    profile_picture = models.ImageField(
        upload_to='riders/profile_pictures/',
        null=True,
        blank=True
    )

    national_id_photo = models.ImageField(
        upload_to='riders/national_ids/',
        null=True,
        blank=True
    )

    bike_plate_number = models.CharField(
        max_length=20,
        unique=True,
        validators=[plate_validator],
        db_index=True
    )

    national_id_number = models.CharField(
        max_length=20,
        unique=True,
        db_index=True
    )

    rider_phone_number = models.CharField(
        max_length=15,
        validators=[phone_validator],
        db_index=True
    )

    # =====================================================
    # LIVE LOCATION TRACKING
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

    last_location_update = models.DateTimeField(
        null=True,
        blank=True
    )

    # =====================================================
    # SECURITY
    # =====================================================

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )

    is_verified = models.BooleanField(
        default=False,
        db_index=True
    )

    is_blacklisted = models.BooleanField(
        default=False,
        db_index=True
    )

    suspicious_activity_score = models.IntegerField(
        default=0
    )

    total_fines = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    # =====================================================
    # SYSTEM FLAGS
    # =====================================================

    is_online = models.BooleanField(
        default=False,
        db_index=True
    )

    is_available = models.BooleanField(
        default=True,
        db_index=True
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

        ordering = ['-created_at']

        indexes = [

            models.Index(fields=['bike_plate_number']),

            models.Index(fields=['national_id_number']),

            models.Index(fields=['rider_phone_number']),

            models.Index(fields=['status']),

            models.Index(fields=['is_verified']),

            models.Index(fields=['latitude', 'longitude']),
        ]

    # =====================================================
    # SAVE
    # =====================================================

    def save(self, *args, **kwargs):

        self.bike_plate_number = self.bike_plate_number.upper()

        super().save(*args, **kwargs)

    # =====================================================
    # STRING
    # =====================================================

    def __str__(self):

        return f"{self.user.username} - {self.bike_plate_number}"


# =========================================================
# REGISTERED RIDER DETAILS
# =========================================================

class RiderDetails(models.Model):

    rider = models.OneToOneField(
        RiderProfile,
        on_delete=models.CASCADE,
        related_name='details'
    )

    residence = models.CharField(
        max_length=255
    )

    village_name = models.CharField(
        max_length=255
    )

    landlord_name = models.CharField(
        max_length=255
    )

    landlord_phone = models.CharField(
        max_length=15,
        validators=[phone_validator]
    )

    father_name = models.CharField(
        max_length=255
    )

    father_phone = models.CharField(
        max_length=15,
        validators=[phone_validator]
    )

    mother_name = models.CharField(
        max_length=255
    )

    mother_phone = models.CharField(
        max_length=15,
        validators=[phone_validator]
    )

    wife_name = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    wife_phone = models.CharField(
        max_length=15,
        null=True,
        blank=True,
        validators=[phone_validator]
    )

    emergency_contact_name = models.CharField(
        max_length=255
    )

    emergency_contact_phone = models.CharField(
        max_length=15,
        validators=[phone_validator]
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):

        return self.rider.user.username


# =========================================================
# GUEST RIDERS (NO STAGE)
# =========================================================

class GuestRider(models.Model):

    STATUS_CHOICES = (

        ('active', 'Active'),

        ('flagged', 'Flagged'),

        ('blacklisted', 'Blacklisted'),
    )

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='guest_rider_profile'
    )

    # =====================================================
    # IDENTITY
    # =====================================================

    profile_picture = models.ImageField(
        upload_to='guest_riders/profile_pictures/',
        null=True,
        blank=True
    )

    bike_plate_number = models.CharField(
        max_length=20,
        unique=True,
        validators=[plate_validator],
        db_index=True
    )

    national_id_number = models.CharField(
        max_length=20,
        unique=True,
        db_index=True
    )

    phone_number = models.CharField(
        max_length=15,
        validators=[phone_validator],
        db_index=True
    )

    # =====================================================
    # MOVEMENT TRACKING
    # =====================================================

    current_area = models.CharField(
        max_length=255,
        db_index=True
    )

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

    last_location_update = models.DateTimeField(
        null=True,
        blank=True
    )

    # =====================================================
    # SECURITY & FINES
    # =====================================================

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        db_index=True
    )

    total_fines = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    suspicious_activity_score = models.IntegerField(
        default=0
    )

    is_blacklisted = models.BooleanField(
        default=False,
        db_index=True
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

        ordering = ['-created_at']

        indexes = [

            models.Index(fields=['bike_plate_number']),

            models.Index(fields=['national_id_number']),

            models.Index(fields=['phone_number']),

            models.Index(fields=['current_area']),

            models.Index(fields=['is_blacklisted']),

            models.Index(fields=['latitude', 'longitude']),
        ]

    # =====================================================
    # SAVE
    # =====================================================

    def save(self, *args, **kwargs):

        self.bike_plate_number = self.bike_plate_number.upper()

        super().save(*args, **kwargs)

    # =====================================================
    # STRING
    # =====================================================

    def __str__(self):

        return f"{self.user.username} - {self.bike_plate_number}"