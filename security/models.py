from django.db import models
from accounts.models import User

class SecurityAlert(models.Model):

    ALERT_TYPES = (

        ('login_anomaly', 'Login Anomaly'),

        ('location_spoof', 'Location Spoofing'),

        ('multiple_accounts', 'Multiple Accounts'),

        ('suspicious_activity', 'Suspicious Activity'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    alert_type = models.CharField(max_length=50, choices=ALERT_TYPES)

    description = models.TextField()

    severity = models.CharField(
        max_length=20,
        default='medium'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:

        indexes = [

            models.Index(fields=['alert_type']),

            models.Index(fields=['severity']),
        ]