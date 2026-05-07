from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator

User = settings.AUTH_USER_MODEL

plate_validator = RegexValidator(
    regex=r'^[A-Z0-9 ]+$',
    message='Plate must contain uppercase letters and numbers only'
)

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

    stage_name = models.CharField(
        max_length=255,
        db_index=True
    )

    residence = models.CharField(max_length=255)

    village_name = models.CharField(
        max_length=255,
        db_index=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )

    is_online = models.BooleanField(default=False)

    is_available = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:

        indexes = [

            models.Index(fields=['bike_plate_number']),

            models.Index(fields=['national_id_number']),

            models.Index(fields=['stage_name']),

            models.Index(fields=['status']),

            models.Index(fields=['village_name']),
        ]

    def save(self, *args, **kwargs):

        self.bike_plate_number = self.bike_plate_number.upper()

        super().save(*args, **kwargs)

    def __str__(self):

        return f"{self.user.email} - {self.bike_plate_number}"