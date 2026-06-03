import logging

from celery import shared_task
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.cache import cache
from .models import SecurityAlert


# =========================================================
# LOGGER
# =========================================================

logger = logging.getLogger("security.tasks")


# =========================================================
# BROADCAST SECURITY ALERT
# =========================================================

@shared_task(bind=True, max_retries=3)
def broadcast_security_alert(self, alert_id):

    try:

        alert = (
            SecurityAlert.objects
            .select_related("user")
            .only(
                "id",
                "user__username",
                "alert_type",
                "reason",
                "severity",
                "resolved",
                "created_at",
            )
            .get(id=alert_id)
        )

        logger.info(
            "Broadcasting security alert | alert_id=%s | user=%s",
            alert.id,
            alert.user_id,
        )

        channel_layer = get_channel_layer()

        if not channel_layer:
            logger.error("Channel layer not configured")
            return "Channel layer missing"

        async_to_sync(channel_layer.group_send)(
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
                },
            },
        )

        logger.info(
            "Security alert broadcast success | alert_id=%s",
            alert.id,
        )

        return f"Broadcasted alert {alert.id}"

    except SecurityAlert.DoesNotExist:

        logger.warning(
            "Security alert not found | alert_id=%s",
            alert_id,
        )

        return "Alert not found"

    except Exception as exc:

        logger.exception(
            "Broadcast failed | alert_id=%s | error=%s",
            alert_id,
            str(exc),
        )

        raise self.retry(exc=exc, countdown=5)


# =========================================================
# CACHE SECURITY ALERTS
# =========================================================

@shared_task
def refresh_security_alert_cache():

    try:

        alerts = list(
            SecurityAlert.objects
            .select_related("user")
            .values(
                "id",
                "user__username",
                "alert_type",
                "severity",
                "resolved",
                "created_at",
            )
            .order_by("-created_at")[:100]
        )

        cache.set(
            "security_alerts_cache",
            alerts,
            timeout=60 * 10,
        )

        logger.info(
            "Security alerts cache refreshed | count=%s",
            len(alerts),
        )

        return "Security alerts cache refreshed"

    except Exception as exc:

        logger.exception(
            "Cache refresh failed | error=%s",
            str(exc),
        )

        return "Cache refresh failed"