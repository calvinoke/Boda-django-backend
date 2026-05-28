from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
import logging

from .models import AuditLog
from .tasks import (
    broadcast_audit_log_task,
    refresh_system_stats_task
)

logger = logging.getLogger(__name__)


# =========================================================
# AUDIT LOG CREATED SIGNAL (PRODUCTION SAFE)
# =========================================================

@receiver(post_save, sender=AuditLog)
def audit_log_created_handler(sender, instance, created, **kwargs):

    if not created:
        return

    try:

        # =========================================
        # ENSURE DB COMMIT BEFORE CELERY RUNS
        # =========================================

        transaction.on_commit(lambda: _trigger_tasks(instance.id))

    except Exception as e:

        logger.error(
            f"Audit signal failed for ID {instance.id}: {str(e)}"
        )


# =========================================================
# TASK TRIGGER FUNCTION (SAFE EXECUTION)
# =========================================================

def _trigger_tasks(audit_id):

    try:

        broadcast_audit_log_task.delay(audit_id)

        refresh_system_stats_task.delay()

    except Exception as e:

        logger.error(
            f"Celery task dispatch failed for audit {audit_id}: {str(e)}"
        )