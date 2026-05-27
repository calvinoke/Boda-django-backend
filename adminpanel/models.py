from django.db import models
from riders.models import RiderProfile


# =========================================================
# RIDER ACTIVITY LOGS
# =========================================================

class RiderActivity(models.Model):

    ACTION_TYPES = [

        ('login', 'Login'),

        ('update_profile', 'Update Profile'),

        ('location_update', 'Location Update'),

        ('emergency_alert', 'Emergency Alert'),

        ('approved', 'Approved'),

        ('suspended', 'Suspended'),
    ]

    rider = models.ForeignKey(

        RiderProfile,

        on_delete=models.CASCADE,

        related_name='activities'
    )

    action = models.CharField(

        max_length=50,

        choices=ACTION_TYPES,

        db_index=True
    )

    description = models.TextField(

        blank=True,

        null=True
    )

    timestamp = models.DateTimeField(

        auto_now_add=True,

        db_index=True
    )

    class Meta:

        ordering = ['-timestamp']

        indexes = [

            models.Index(fields=['action']),

            models.Index(fields=['timestamp']),
        ]

    def __str__(self):

        return f"{self.rider.user.email} - {self.action}"


# =========================================================
# SYSTEM LOGS
# =========================================================

class SystemLog(models.Model):

    LEVELS = [

        ('info', 'Info'),

        ('warning', 'Warning'),

        ('error', 'Error'),
    ]

    message = models.TextField()

    level = models.CharField(

        max_length=10,

        choices=LEVELS,

        db_index=True
    )

    created_at = models.DateTimeField(

        auto_now_add=True,

        db_index=True
    )

    class Meta:

        ordering = ['-created_at']

    def __str__(self):

        return self.level

