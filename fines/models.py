from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator


User = settings.AUTH_USER_MODEL


# =========================================================
# FINE REASONS (CONFIGURABLE)
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

    def __str__(self):
        return self.name


# =========================================================
# MAIN FINE MODEL
# =========================================================

class Fine(models.Model):

    OFFENDER_TYPE = (
        ('rider', 'Rider'),
        ('guest_rider', 'Guest Rider'),
    )

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('disputed', 'Disputed'),
        ('cancelled', 'Cancelled'),
    )

    # =====================================================
    # WHO ISSUED THE FINE
    # =====================================================

    issued_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='issued_fines'
    )

    # =====================================================
    # OFFENDER (GENERIC DESIGN)
    # =====================================================

    rider = models.ForeignKey(
        'riders.RiderProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='fines'
    )

    guest_rider = models.ForeignKey(
        'riders.GuestRider',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='fines'
    )

    offender_type = models.CharField(
        max_length=20,
        choices=OFFENDER_TYPE,
        db_index=True
    )

    # =====================================================
    # FINE DETAILS
    # =====================================================

    fine_type = models.ForeignKey(
        FineType,
        on_delete=models.SET_NULL,
        null=True,
        related_name='fines'
    )

    reason = models.TextField()

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    # =====================================================
    # STAGE CONTEXT
    # =====================================================

    stage = models.ForeignKey(
        'stages.Stage',
        on_delete=models.SET_NULL,
        null=True,
        related_name='fines'
    )

    # =====================================================
    # LOCATION (FOR ENFORCEMENT)
    # =====================================================

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

    # =====================================================
    # EVIDENCE
    # =====================================================

    evidence_image = models.ImageField(
        upload_to='fines/evidence/',
        null=True,
        blank=True
    )

    # =====================================================
    # STATUS
    # =====================================================

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )

    # =====================================================
    # PAYMENT TRACKING
    # =====================================================

    paid_at = models.DateTimeField(null=True, blank=True)

    payment_reference = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    # =====================================================
    # AUDIT
    # =====================================================

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.offender_type} - {self.amount} - {self.status}"