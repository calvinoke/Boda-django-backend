import logging

from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import SecurityAlert
from .serializers import SecurityAlertSerializer
from .tasks import ( broadcast_security_alert, refresh_security_alert_cache,)

# =========================================================
# LOGGER
# =========================================================

logger = logging.getLogger("security.views")


# =========================================================
# SECURITY ALERT VIEWSET
# =========================================================

class SecurityAlertViewSet(viewsets.ModelViewSet):

    serializer_class = SecurityAlertSerializer
    permission_classes = [IsAuthenticated]

    queryset = SecurityAlert.objects.select_related(
        "user",
        "resolved_by",
    )

    # =====================================================
    # QUERYSET FILTERING
    # =====================================================

    def get_queryset(self):

        user = self.request.user

        try:

            if (
                user.is_staff
                or (hasattr(user, "role") and user.role == "super_admin")
            ):

                logger.info(
                    "SecurityAlert queryset (admin) | user_id=%s",
                    user.id,
                )

                return self.queryset.all()

            logger.info(
                "SecurityAlert queryset (user scoped) | user_id=%s",
                user.id,
            )

            return self.queryset.filter(user=user)

        except Exception as exc:

            logger.exception(
                "Error building queryset | user_id=%s | error=%s",
                user.id,
                str(exc),
            )

            return SecurityAlert.objects.none()

    # =====================================================
    # CREATE ALERT
    # =====================================================

    def perform_create(self, serializer):

        try:

            alert = serializer.save(user=self.request.user)

            logger.info(
                "SecurityAlert created | alert_id=%s | user_id=%s",
                alert.id,
                self.request.user.id,
            )

            broadcast_security_alert.delay(alert.id)
            refresh_security_alert_cache.delay()

            logger.info(
                "SecurityAlert tasks queued | alert_id=%s",
                alert.id,
            )

        except Exception as exc:

            logger.exception(
                "Failed to create SecurityAlert | user_id=%s | error=%s",
                self.request.user.id,
                str(exc),
            )

            raise

    # =====================================================
    # RESOLVE ALERT
    # =====================================================

    @action(detail=True, methods=["post"])
    def resolve_alert(self, request, pk=None):

        try:

            alert = self.get_object()

            if alert.resolved:

                logger.warning(
                    "Alert already resolved | alert_id=%s | user_id=%s",
                    alert.id,
                    request.user.id,
                )

                return Response(
                    {"message": "Alert already resolved"},
                    status=400,
                )

            alert.resolved = True
            alert.resolved_by = request.user
            alert.resolved_at = timezone.now()

            alert.save()

            logger.info(
                "SecurityAlert resolved | alert_id=%s | resolved_by=%s",
                alert.id,
                request.user.id,
            )

            broadcast_security_alert.delay(alert.id)
            refresh_security_alert_cache.delay()

            return Response(
                {
                    "message": "Alert resolved successfully",
                    "alert_id": alert.id,
                }
            )

        except Exception as exc:

            logger.exception(
                "Failed to resolve alert | alert_id=%s | error=%s",
                pk,
                str(exc),
            )

            return Response(
                {"error": "Failed to resolve alert"},
                status=500,
            )