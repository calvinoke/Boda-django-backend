from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


# =========================================================
# RIDER LOCATION
# =========================================================

class RiderLocation(models.Model):

    # =====================================================
    # WHO IS BEING TRACKED (STRICT ONE-OF RULE)
    # =====================================================

    rider = models.ForeignKey(
        'riders.RiderProfile',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='locations',
        db_index=True
    )

    guest_rider = models.ForeignKey(
        'riders.GuestRider',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='locations',
        db_index=True
    )

    # =====================================================
    # LOCATION DATA (VALIDATED)
    # =====================================================

    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        validators=[MinValueValidator(-90), MaxValueValidator(90)]
    )

    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        validators=[MinValueValidator(-180), MaxValueValidator(180)]
    )

    speed = models.FloatField(
        default=0,
        validators=[MinValueValidator(0)]
    )

    heading = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(360)]
    )

    # =====================================================
    # CONTEXT
    # =====================================================

    is_suspicious = models.BooleanField(default=False, db_index=True)

    detected_violation = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_index=True
    )

    # =====================================================
    # TIME
    # =====================================================

    recorded_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['rider', 'recorded_at']),
            models.Index(fields=['guest_rider', 'recorded_at']),
        ]

    # =====================================================
    # DATA INTEGRITY RULE
    # =====================================================

    def clean(self):

        from django.core.exceptions import ValidationError

        if not self.rider and not self.guest_rider:
            raise ValidationError("Location must belong to a rider or guest rider")

        if self.rider and self.guest_rider:
            raise ValidationError("Location cannot belong to both rider and guest rider")


# =========================================================
# SUSPICIOUS EVENT
# =========================================================

class SuspiciousEvent(models.Model):

    EVENT_TYPES = (
        ('out_of_stage', 'Out of Stage'),
        ('unknown_area', 'Unknown Area'),
        ('speed_violation', 'Speed Violation'),
        ('no_movement', 'No Movement'),
        ('guest_rider_hotspot', 'Guest Rider Hotspot'),
    )

    rider = models.ForeignKey(
        'riders.RiderProfile',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        db_index=True
    )

    guest_rider = models.ForeignKey(
        'riders.GuestRider',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        db_index=True
    )

    event_type = models.CharField(
        max_length=50,
        choices=EVENT_TYPES,
        db_index=True
    )

    description = models.TextField()

    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )

    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )

    auto_fine_triggered = models.BooleanField(default=False, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['event_type', 'created_at']),
            models.Index(fields=['auto_fine_triggered']),
        ]

    # =====================================================
    # DATA VALIDATION RULE
    # =====================================================

    def clean(self):

        from django.core.exceptions import ValidationError

        if not self.rider and not self.guest_rider:
            raise ValidationError("Event must belong to rider or guest rider")

        if self.rider and self.guest_rider:
            raise ValidationError("Event cannot belong to both rider and guest rider")