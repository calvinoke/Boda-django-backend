from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL

class Announcement(models.Model):

    ANNOUNCEMENT_TYPES = (

        ('death', 'Death'),

        ('meeting', 'Meeting'),

        ('security', 'Security'),

        ('admin_change', 'Administration Change'),

        ('general', 'General'),
    )

    title = models.CharField(
        max_length=255,
        db_index=True
    )

    message = models.TextField()

    announcement_type = models.CharField(
        max_length=50,
        choices=ANNOUNCEMENT_TYPES,
        db_index=True
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )

    is_active = models.BooleanField(
        default=True,
        db_index=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )

    class Meta:

        ordering = ['-created_at']

        indexes = [

            models.Index(fields=['announcement_type']),

            models.Index(fields=['is_active']),

            models.Index(fields=['created_at']),
        ]

    def __str__(self):

        return self.title


    
class Condolence(models.Model):

    # =====================================================
    # STATUS CHOICES
    # =====================================================

    STATUS_CHOICES = (

        ('pending', 'Pending'),

        ('verified', 'Verified'),

        ('rejected', 'Rejected'),
    )

    # =====================================================
    # TARGET ROLE CHOICES
    # =====================================================

    ROLE_CHOICES = (

        ('super_admin', 'Super Admin'),

        ('stage_chairman', 'Stage Chairman'),

        ('stage_secretary', 'Stage Secretary'),

        ('stage_defense', 'Stage Defense'),

        ('rider', 'Rider'),

        ('guest_rider', 'Guest Rider'),
    )

    # =====================================================
    # RELATIONSHIPS
    # =====================================================

    rider = models.ForeignKey(
        'riders.RiderProfile',
        on_delete=models.CASCADE,
        related_name='condolences'
    )

    reported_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='reported_condolences'
    )

    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_condolences'
    )

    # =====================================================
    # CONDOLENCE DETAILS
    # =====================================================

    description = models.TextField()

    burial_location = models.CharField(
        max_length=255
    )

    date_of_death = models.DateField(
        db_index=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )

    target_role = models.CharField(
        max_length=30,
        choices=ROLE_CHOICES,
        null=True,
        blank=True,
        db_index=True
    )

    # =====================================================
    # TIMESTAMPS
    # =====================================================

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )

    # =====================================================
    # META
    # =====================================================

    class Meta:

        ordering = ['-created_at']

        indexes = [

            models.Index(fields=['status']),

            models.Index(fields=['date_of_death']),

            models.Index(fields=['target_role']),
        ]

    # =====================================================
    # STRING REPRESENTATION
    # =====================================================

    def __str__(self):

        return (
            f"Condolence - "
            f"{self.rider.user.email}"
        )