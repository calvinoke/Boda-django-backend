from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL


# =========================================================
# SECURITY ALERT MODEL
# =========================================================

class SecurityAlert(models.Model):

    SEVERITY = (

        ('low', 'Low'),

        ('medium', 'Medium'),

        ('high', 'High'),

        ('critical', 'Critical'),
    )

    ALERT_TYPES = (

        ('suspicious_login', 'Suspicious Login'),

        ('multiple_failed_logins', 'Multiple Failed Logins'),

        ('location_violation', 'Location Violation'),

        ('account_takeover', 'Account Takeover'),

        ('fake_identity', 'Fake Identity'),

        ('general', 'General'),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='security_alerts',
        db_index=True
    )

    alert_type = models.CharField(
        max_length=50,
        choices=ALERT_TYPES,
        default='general',
        db_index=True
    )

    reason = models.TextField()

    severity = models.CharField(
        max_length=20,
        choices=SEVERITY,
        db_index=True
    )

    auto_flagged = models.BooleanField(
        default=False,
        db_index=True
    )

    resolved = models.BooleanField(
        default=False,
        db_index=True
    )

    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_security_alerts'
    )

    resolved_at = models.DateTimeField(
        null=True,
        blank=True
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True
    )

    device_info = models.TextField(
        null=True,
        blank=True
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

            models.Index(fields=['severity', 'resolved']),

            models.Index(fields=['alert_type']),

            models.Index(fields=['created_at']),
        ]

    def __str__(self):

        return f"{self.user} - {self.severity}"