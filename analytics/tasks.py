import logging
from celery import shared_task
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.cache import cache
from .models import AuditLog
from .services import cache_system_stats


# =========================================================
# LOGGER
# =========================================================

logger = logging.getLogger(__name__)


# =========================================================
# BROADCAST AUDIT LOG (PRODUCTION READY)
# =========================================================

@shared_task(bind=True, max_retries=3)
def broadcast_audit_log_task(self, audit_log_id):

    try:

        logger.info(f"Broadcast audit log task started: {audit_log_id}")

        audit_log = AuditLog.objects.select_related('user').get(
            id=audit_log_id
        )

        channel_layer = get_channel_layer()

        async_to_sync(channel_layer.group_send)(
            "admin_dashboard",
            {
                "type": "send_admin_update",
                "message": {
                    "id": audit_log.id,
                    "action": audit_log.action,
                    "entity": audit_log.entity,
                    "entity_id": audit_log.entity_id,
                    "timestamp": str(audit_log.timestamp),
                }
            }
        )

        logger.info(f"Audit log broadcast successful: {audit_log_id}")

    except AuditLog.DoesNotExist:

        logger.warning(f"AuditLog not found: {audit_log_id}")

    except Exception as exc:

        logger.error(
            f"Broadcast audit log failed: {audit_log_id} - {str(exc)}",
            exc_info=True
        )

        raise self.retry(exc=exc, countdown=5)


# =========================================================
# REFRESH SYSTEM STATS (PRODUCTION READY)
# =========================================================

@shared_task
def refresh_system_stats_task():

    try:

        logger.info("Refreshing system stats cache")

        stats = cache_system_stats()

        channel_layer = get_channel_layer()

        async_to_sync(channel_layer.group_send)(
            "admin_stats",
            {
                "type": "send_stats_update",
                "message": stats,
            }
        )

        logger.info("System stats broadcast successful")

    except Exception as exc:

        logger.error(
            f"System stats refresh failed: {str(exc)}",
            exc_info=True
        )