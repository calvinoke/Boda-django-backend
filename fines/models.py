import logging
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db.models import Q

logger = logging.getLogger("fines.models")

User = settings.AUTH_USER_MODEL


# =========================================================
# FINE TYPES
# =========================================================

class FineType(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)

    default_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return self.name


# =========================================================
# MAIN FINE MODEL
# =========================================================

class Fine(models.Model):

    OFFENDER_TYPE = (
        ("rider", "Rider"),
        ("guest_rider", "Guest Rider"),
    )

    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("disputed", "Disputed"),
        ("cancelled", "Cancelled"),
    )

    issued_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="issued_fines",
        db_index=True
    )

    rider = models.ForeignKey(
        "riders.RiderProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="fines",
        db_index=True
    )

    guest_rider = models.ForeignKey(
        "riders.GuestRider",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="fines",
        db_index=True
    )

    offender_type = models.CharField(
        max_length=20,
        choices=OFFENDER_TYPE,
        db_index=True
    )

    fine_type = models.ForeignKey(
        FineType,
        on_delete=models.SET_NULL,
        null=True,
        related_name="fines",
        db_index=True
    )

    reason = models.TextField()

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    stage = models.ForeignKey(
        "stages.Stage",
        on_delete=models.SET_NULL,
        null=True,
        related_name="fines",
        db_index=True
    )

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

    evidence_image = models.ImageField(
        upload_to="fines/evidence/",
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        db_index=True
    )

    paid_at = models.DateTimeField(null=True, blank=True)

    payment_reference = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    # =====================================================
    # META + DATABASE CONSTRAINTS (FIXED)
    # =====================================================

    class Meta:
        ordering = ["-created_at"]

        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["offender_type", "status"]),
            models.Index(fields=["stage", "status"]),
            models.Index(fields=["fine_type"]),
            models.Index(fields=["created_at"]),
        ]

        constraints = [
            models.CheckConstraint(
                name="fine_offender_consistency",
                condition=(
                    Q(
                        offender_type="rider",
                        rider__isnull=False,
                        guest_rider__isnull=True
                    )
                    |
                    Q(
                        offender_type="guest_rider",
                        guest_rider__isnull=False,
                        rider__isnull=True
                    )
                ),
            )
        ]

    # =====================================================
    # CLEAN VALIDATION (SAFE + LIGHTWEIGHT)
    # =====================================================

    def clean(self):
        if self.offender_type == "rider" and not self.rider:
            raise ValueError("Rider is required for rider fines")

        if self.offender_type == "guest_rider" and not self.guest_rider:
            raise ValueError("Guest rider is required for guest fines")

    def __str__(self):
        return f"{self.offender_type} | {self.amount} | {self.status}"