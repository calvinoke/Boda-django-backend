from django.db import models
from riders.models import RiderProfile

class RiderLocation(models.Model):

    rider = models.OneToOneField(
        RiderProfile,
        on_delete=models.CASCADE,
        related_name='current_location'
    )

    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        db_index=True
    )

    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        db_index=True
    )

    accuracy = models.FloatField(
        null=True,
        blank=True
    )

    speed = models.FloatField(
        default=0
    )

    heading = models.FloatField(
        default=0
    )

    is_online = models.BooleanField(
        default=False,
        db_index=True
    )

    last_updated = models.DateTimeField(
        auto_now=True,
        db_index=True
    )

    class Meta:

        indexes = [

            models.Index(fields=['is_online']),

            models.Index(fields=['last_updated']),
        ]

    def __str__(self):

        return f"{self.rider.user.email} location"