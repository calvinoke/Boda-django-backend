from django.db import models
from riders.models import RiderProfile

class RiderActivity(models.Model):
    ACTION_TYPES = [
        ('login', 'Login'),
        ('update_profile', 'Update Profile'),
        ('location_update', 'Location Update'),
        ('emergency_alert', 'Emergency Alert'),
    ]

    rider = models.ForeignKey(RiderProfile, on_delete=models.CASCADE)
    action = models.CharField(max_length=50, choices=ACTION_TYPES)

    description = models.TextField(blank=True, null=True)

    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.rider.user.email} - {self.action}"
    


class SystemLog(models.Model):
    LEVELS = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
    ]

    message = models.TextField()
    level = models.CharField(max_length=10, choices=LEVELS)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.level



class TestModel(models.Model):
    name = models.CharField(max_length=100)