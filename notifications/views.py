import logging

from django.core.cache import cache
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Notification
from .serializers import NotificationSerializer
from .tasks import refresh_notifications_cache


# =========================================================
# LOGGER
# =========================================================

logger = logging.getLogger("notifications.api")


class NotificationViewSet(viewsets.ModelViewSet):

    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    # =====================================================
    # GET QUERYSET
    # =====================================================

    def get_queryset(self):

        user = self.request.user

        try:

            # ADMIN USERS
            if hasattr(user, "role") and user.role in [
                "super_admin",
                "stage_chairman",
                "stage_secretary",
                "stage_defense",
            ]:

                logger.info(f"Admin access notifications | user_id={user.id}")
                return Notification.objects.all()

            # NORMAL USERS
            logger.info(f"User access notifications | user_id={user.id}")

            return Notification.objects.filter(user=user)

        except Exception as exc:

            logger.error(
                f"Notification queryset error | user_id={user.id} | error={str(exc)}"
            )

            return Notification.objects.none()

    # =====================================================
    # MARK AS READ
    # =====================================================

    @action(detail=True, methods=["post"])
    def mark_as_read(self, request, pk=None):

        try:

            notification = self.get_object()
            notification.is_read = True
            notification.save()

            logger.info(
                f"Notification marked as read | notification_id={notification.id} | user_id={request.user.id}"
            )

            try:
                refresh_notifications_cache.delay(request.user.id)
                logger.info(
                    f"Cache refresh triggered | user_id={request.user.id}"
                )
            except Exception as exc:
                logger.error(
                    f"Cache refresh failed | user_id={request.user.id} | error={str(exc)}"
                )

            return Response({
                "message": "Notification marked as read"
            })

        except Exception as exc:

            logger.error(
                f"Mark as read failed | user_id={request.user.id} | error={str(exc)}"
            )

            return Response(
                {"error": "Failed to mark notification as read"},
                status=500
            )

    # =====================================================
    # GET CACHED NOTIFICATIONS
    # =====================================================

    @action(detail=False, methods=["get"])
    def cached(self, request):

        try:

            cache_key = f"user_notifications_{request.user.id}"
            data = cache.get(cache_key)

            if not data:

                logger.info(
                    f"Cache miss for notifications | user_id={request.user.id}"
                )

                try:
                    refresh_notifications_cache.delay(request.user.id)
                except Exception as exc:
                    logger.error(
                        f"Cache rebuild failed | user_id={request.user.id} | error={str(exc)}"
                    )

                return Response({
                    "message": "Cache rebuilding"
                })

            logger.info(
                f"Cache hit for notifications | user_id={request.user.id}"
            )

            return Response(data)

        except Exception as exc:

            logger.error(
                f"Cached notifications error | user_id={request.user.id} | error={str(exc)}"
            )

            return Response(
                {"error": "Failed to fetch cached notifications"},
                status=500
            )