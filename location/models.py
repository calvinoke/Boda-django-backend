from django.db import models
from riders.models import RiderProfile,GuestRider


class RiderLocation(models.Model):

    # =====================================================
    # WHO IS BEING TRACKED
    # =====================================================

    rider = models.ForeignKey(
        'riders.RiderProfile',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='locations'
    )

    guest_rider = models.ForeignKey(
        'riders.GuestRider',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='locations'
    )

    # =====================================================
    # LOCATION DATA
    # =====================================================

    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6
    )

    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6
    )

    speed = models.FloatField(default=0)  # km/h

    heading = models.FloatField(null=True, blank=True)

    # =====================================================
    # CONTEXT
    # =====================================================

    is_suspicious = models.BooleanField(default=False)

    detected_violation = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    # =====================================================
    # TIME
    # =====================================================

    recorded_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:

        ordering = ['-recorded_at']



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
        on_delete=models.CASCADE
    )

    guest_rider = models.ForeignKey(
        'riders.GuestRider',
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )

    event_type = models.CharField(
        max_length=50,
        choices=EVENT_TYPES
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

    auto_fine_triggered = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)