from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL


class Notification(models.Model):

    NOTIFICATION_TYPES = (

        ('announcement', 'Announcement'),

        ('verification', 'Verification'),

        ('emergency', 'Emergency'),

        ('security', 'Security'),

        ('general', 'General'),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications'
    )

    title = models.CharField(
        max_length=255
    )

    message = models.TextField()

    notification_type = models.CharField(
        max_length=50,
        choices=NOTIFICATION_TYPES,
        db_index=True
    )

    is_read = models.BooleanField(
        default=False,
        db_index=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )

    class Meta:

        ordering = ['-created_at']

        indexes = [

            models.Index(fields=['notification_type']),

            models.Index(fields=['is_read']),

            models.Index(fields=['created_at']),
        ]

    def __str__(self):

        return f"{self.user.username} - {self.title}"