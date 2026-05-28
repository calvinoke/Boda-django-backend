from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL


# =========================================================
# AUDIT LOG MODEL (PRODUCTION READY)
# =========================================================

class AuditLog(models.Model):

    # =====================================================
    # ACTION TYPES (STANDARDIZED FOR PRODUCTION)
    # =====================================================

    ACTION_CHOICES = [

        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),

        ('login', 'Login'),
        ('logout', 'Logout'),

        ('approve', 'Approve'),
        ('suspend', 'Suspend'),

        ('verification', 'Verification'),
        ('security_alert', 'Security Alert'),
    ]

    # =====================================================
    # USER WHO PERFORMED ACTION
    # =====================================================

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )

    # =====================================================
    # ACTION DETAILS
    # =====================================================

    action = models.CharField(
        max_length=50,
        choices=ACTION_CHOICES,
        db_index=True
    )

    entity = models.CharField(
        max_length=255,
        db_index=True
    )

    entity_id = models.IntegerField(
        null=True,
        blank=True,
        db_index=True
    )

    # =====================================================
    # SECURITY CONTEXT
    # =====================================================

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True
    )

    user_agent = models.TextField(
        null=True,
        blank=True
    )

    request_method = models.CharField(
        max_length=10,
        null=True,
        blank=True
    )

    path = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    # =====================================================
    # TIMESTAMP
    # =====================================================

    timestamp = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )

    # =====================================================
    # META CONFIGURATION
    # =====================================================

    class Meta:

        ordering = ['-timestamp']

        indexes = [

            models.Index(fields=['action']),

            models.Index(fields=['entity', 'entity_id']),

            models.Index(fields=['timestamp']),
        ]

    # =====================================================
    # STRING REPRESENTATION
    # =====================================================

    def __str__(self):

        return f"{self.action} - {self.entity}"