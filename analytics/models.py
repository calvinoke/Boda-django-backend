from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL


class AuditLog(models.Model):

    user = models.ForeignKey(

        User,

        on_delete=models.SET_NULL,

        null=True
    )

    action = models.CharField(
        max_length=255
    )

    entity = models.CharField(
        max_length=255
    )

    entity_id = models.IntegerField(
        null=True,
        blank=True
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True
    )

    timestamp = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:

        ordering = ['-timestamp']

        indexes = [

            models.Index(fields=['action']),

            models.Index(fields=['timestamp']),
        ]

    def __str__(self):

        return f"{self.action} - {self.entity}"