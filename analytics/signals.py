from django.db.models.signals import (post_save)
from django.dispatch import receiver
from .models import AuditLog
from .tasks import (broadcast_audit_log_task,refresh_system_stats_task)


# =========================================================
# AUDIT LOG CREATED
# =========================================================

@receiver(
    post_save,
    sender=AuditLog
)
def audit_log_created_handler(
    sender,
    instance,
    created,
    **kwargs
):

    if created:

        broadcast_audit_log_task.delay(
            instance.id
        )

        refresh_system_stats_task.delay()