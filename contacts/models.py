from django.db import models

from riders.models import RiderProfile


class EmergencyContact(models.Model):

    CONTACT_TYPES = (

        ('wife', 'Wife'),

        ('father', 'Father'),

        ('mother', 'Mother'),

        ('stage_chairman', 'Stage Chairman'),

        ('defence', 'Defence'),

        ('lc1', 'LC1 Chairman'),

        ('landlord', 'Landlord'),
    )

    rider = models.ForeignKey(
        RiderProfile,
        on_delete=models.CASCADE,
        related_name='emergency_contacts'
    )

    name = models.CharField(
        max_length=255
    )

    phone_number = models.CharField(
        max_length=15,
        db_index=True
    )

    relationship = models.CharField(
        max_length=50,
        choices=CONTACT_TYPES,
        db_index=True
    )

    village = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    is_primary = models.BooleanField(
        default=False
    )

    is_active = models.BooleanField(
        default=True,
        db_index=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:

        ordering = ['-created_at']

        indexes = [

            models.Index(fields=['phone_number']),

            models.Index(fields=['relationship']),

            models.Index(fields=['is_active']),
        ]

    def __str__(self):

        return f"{self.name} ({self.relationship})"