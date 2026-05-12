from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL


class SecurityAlert(models.Model):

    SEVERITY = (

        ('low', 'Low'),

        ('medium', 'Medium'),

        ('high', 'High'),

        ('critical', 'Critical'),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='security_alerts'
    )

    reason = models.TextField()

    severity = models.CharField(
        max_length=20,
        choices=SEVERITY,
        db_index=True
    )

    auto_flagged = models.BooleanField(default=False)

    resolved = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.severity}"