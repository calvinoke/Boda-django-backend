from django.db import models
from riders.models import RiderProfile

class RiderVerification(models.Model):

    rider = models.OneToOneField(
        RiderProfile,
        on_delete=models.CASCADE,
        related_name='verification'
    )

    national_id_front = models.ImageField(
        upload_to='verification/national_ids/'
    )

    national_id_back = models.ImageField(
        upload_to='verification/national_ids/'
    )

    driving_license = models.ImageField(
        upload_to='verification/licenses/'
    )

    passport_photo = models.ImageField(
        upload_to='verification/photos/'
    )

    police_clearance = models.ImageField(
        upload_to='verification/police/'
    )

    is_verified = models.BooleanField(
        default=False,
        db_index=True
    )

    verified_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    verified_at = models.DateTimeField(
        null=True,
        blank=True
    )

    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:

        indexes = [

            models.Index(fields=['is_verified']),
        ]

    def __str__(self):

        return f"Verification - {self.rider.user.email}"
    

from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL


class VerificationRequest(models.Model):

    STATUS = (

        ('pending', 'Pending'),

        ('approved', 'Approved'),

        ('rejected', 'Rejected'),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='verification_requests'
    )

    submitted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='submitted_verifications'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default='pending',
        db_index=True
    )

    notes = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)