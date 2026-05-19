from celery import shared_task
from asgiref.sync import async_to_sync
from channels.layers import (
    get_channel_layer
)
from django.core.cache import cache
from .models import AuditLog
from .services import (
    cache_system_stats
)


# =========================================================
# BROADCAST AUDIT LOG
# =========================================================

@shared_task
def broadcast_audit_log_task(
    audit_log_id
):

    try:

        audit_log = AuditLog.objects.select_related(
            'user'
        ).get(id=audit_log_id)

        channel_layer = get_channel_layer()

        async_to_sync(
            channel_layer.group_send
        )(

            "admin_dashboard",

            {

                "type": "send_admin_update",

                "message": {

                    "id": audit_log.id,

                    "action": audit_log.action,

                    "entity": audit_log.entity,

                    "entity_id":
                        audit_log.entity_id,

                    "timestamp":
                        str(audit_log.timestamp),
                }
            }
        )

    except AuditLog.DoesNotExist:
        pass


# =========================================================
# REFRESH SYSTEM STATS
# =========================================================

@shared_task
def refresh_system_stats_task():

    stats = cache_system_stats()

    channel_layer = get_channel_layer()

    async_to_sync(
        channel_layer.group_send
    )(

        "admin_stats",

        {

            "type": "send_stats_update",

            "message": stats,
        }
    )