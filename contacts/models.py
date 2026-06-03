import re
import logging

from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Q
from riders.models import RiderProfile

logger = logging.getLogger("emergency_contacts")


# =========================================================
# PHONE NORMALIZATION
# =========================================================

def normalize_phone(phone: str) -> str:
    """
    Normalizes Ugandan phone numbers to +256 format
    """
    if not phone:
        raise ValidationError("Phone number is required.")

    phone = phone.strip()

    # 07XXXXXXXX → +2567XXXXXXXX
    if re.match(r"^0[0-9]{9}$", phone):
        return "+256" + phone[1:]

    # Already correct format
    if re.match(r"^\+256[0-9]{9}$", phone):
        return phone

    raise ValidationError("Invalid phone format. Use 07XXXXXXXX or +2567XXXXXXXX")


# =========================================================
# EMERGENCY CONTACT MODEL
# =========================================================

class EmergencyContact(models.Model):

    CONTACT_TYPES = (
        ("wife", "Wife"),
        ("father", "Father"),
        ("mother", "Mother"),
        ("stage_chairman", "Stage Chairman"),
        ("defence", "Defence"),
        ("lc1", "LC1 Chairman"),
        ("landlord", "Landlord"),
    )

    rider = models.ForeignKey(
        RiderProfile,
        on_delete=models.CASCADE,
        related_name="emergency_contacts",
        db_index=True
    )

    name = models.CharField(max_length=255)

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

    is_primary = models.BooleanField(default=False, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    # =========================================================
    # META
    # =========================================================

    class Meta:
        ordering = ["-created_at"]

        indexes = [
            models.Index(fields=["rider", "is_active"]),
            models.Index(fields=["phone_number"]),
            models.Index(fields=["relationship"]),
        ]

        constraints = [
            models.UniqueConstraint(
                fields=["rider"],
                condition=Q(is_primary=True),
                name="unique_primary_emergency_contact_per_rider"
            )
        ]

    # =========================================================
    # VALIDATION
    # =========================================================

    def clean(self):
        self.phone_number = normalize_phone(self.phone_number)

        # Ensure only one primary contact per rider
        if self.is_primary:
            exists = EmergencyContact.objects.filter(
                rider=self.rider,
                is_primary=True
            ).exclude(pk=self.pk).exists()

            if exists:
                raise ValidationError(
                    "Each rider can only have one primary emergency contact."
                )

    # =========================================================
    # SAVE OVERRIDE
    # =========================================================

    def save(self, *args, **kwargs):
        try:
            self.full_clean()
            super().save(*args, **kwargs)

            logger.info(
                "Emergency contact saved | rider_id=%s | name=%s | primary=%s",
                self.rider_id,
                self.name,
                self.is_primary
            )

        except Exception as exc:
            logger.exception(
                "Failed saving emergency contact | rider_id=%s | name=%s",
                getattr(self, "rider_id", None),
                self.name
            )
            raise

    # =========================================================
    # STRING
    # =========================================================

    def __str__(self):
        return f"{self.name} ({self.relationship})"