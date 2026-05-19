from celery import shared_task
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.cache import cache
from .models import SecurityAlert


# =========================================================
# BROADCAST SECURITY ALERT
# =========================================================

@shared_task
def broadcast_security_alert(alert_id):

    try:

        alert = SecurityAlert.objects.select_related(
            'user'
        ).get(id=alert_id)

        channel_layer = get_channel_layer()

        async_to_sync(
            channel_layer.group_send
        )(

            "security_alerts",

            {

                "type": "send_security_alert",

                "message": {

                    "id": alert.id,

                    "user": alert.user.username,

                    "alert_type": alert.alert_type,

                    "reason": alert.reason,

                    "severity": alert.severity,

                    "resolved": alert.resolved,

                    "created_at": str(alert.created_at),
                }
            }
        )

    except SecurityAlert.DoesNotExist:

        return "Alert not found"


# =========================================================
# CACHE SECURITY ALERTS
# =========================================================

@shared_task
def refresh_security_alert_cache():

    alerts = list(

        SecurityAlert.objects.select_related(
            'user'
        ).values(

            'id',

            'user__username',

            'alert_type',

            'severity',

            'resolved',

            'created_at'
        )[:100]
    )

    cache.set(

        'security_alerts_cache',

        alerts,

        timeout=60 * 10
    )

    return "Security alerts cache refreshed"