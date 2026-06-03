from django.db import models
from django.conf import settings
from django.db.models import Q

User = settings.AUTH_USER_MODEL


# =========================================================
# SECURITY ALERT MODEL
# =========================================================

class SecurityAlert(models.Model):

    SEVERITY = (
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("critical", "Critical"),
    )

    ALERT_TYPES = (
        ("suspicious_login", "Suspicious Login"),
        ("multiple_failed_logins", "Multiple Failed Logins"),
        ("location_violation", "Location Violation"),
        ("account_takeover", "Account Takeover"),
        ("fake_identity", "Fake Identity"),
        ("general", "General"),
    )

    # =====================================================
    # USER
    # =====================================================

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="security_alerts",
        db_index=True,
    )

    # =====================================================
    # ALERT DETAILS
    # =====================================================

    alert_type = models.CharField(
        max_length=50,
        choices=ALERT_TYPES,
        default="general",
        db_index=True,
    )

    reason = models.TextField()

    severity = models.CharField(
        max_length=20,
        choices=SEVERITY,
        db_index=True,
    )

    auto_flagged = models.BooleanField(
        default=False,
        db_index=True,
    )

    # =====================================================
    # RESOLUTION
    # =====================================================

    resolved = models.BooleanField(
        default=False,
        db_index=True,
    )

    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resolved_security_alerts",
    )

    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    resolution_notes = models.TextField(
        null=True,
        blank=True,
    )

    # =====================================================
    # DEVICE / NETWORK INFORMATION
    # =====================================================

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
    )

    device_info = models.TextField(
        null=True,
        blank=True,
    )

    # =====================================================
    # OPTIONAL GPS INFORMATION
    # =====================================================

    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )

    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )

    # =====================================================
    # AUDIT FIELDS
    # =====================================================

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    # =====================================================
    # META
    # =====================================================

    class Meta:

        ordering = ["-created_at"]

        indexes = [
            models.Index(
                fields=["user", "resolved"]
            ),

            models.Index(
                fields=[
                    "user",
                    "resolved",
                    "created_at"
                ]
            ),

            models.Index(
                fields=[
                    "severity",
                    "resolved"
                ]
            ),

            models.Index(
                fields=["alert_type"]
            ),

            models.Index(
                fields=["created_at"]
            ),
        ]

        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(resolved=False)
                    |
                    (
                        Q(resolved=True)
                        &
                        Q(resolved_by__isnull=False)
                        &
                        Q(resolved_at__isnull=False)
                    )
                ),
                name="security_alert_resolution_integrity",
            )
        ]

    # =====================================================
    # STRING REPRESENTATION
    # =====================================================

    def __str__(self):

        return (
            f"Alert #{self.id} | "
            f"{self.user} | "
            f"{self.severity}"
        )