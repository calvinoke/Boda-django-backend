import logging

from django.core.cache import cache
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import RiderLocation, SuspiciousEvent
from .serializers import RiderLocationSerializer, SuspiciousEventSerializer
from .tasks import save_location_task

logger = logging.getLogger("gps.api")


# =========================================================
# LOCATION VIEWSET
# =========================================================

class LocationViewSet(viewsets.ModelViewSet):

    serializer_class = RiderLocationSerializer
    permission_classes = [IsAuthenticated]

    # =====================================================
    # QUERYSET
    # =====================================================

    def get_queryset(self):

        try:

            cache_key = "live_locations_v1"
            cached = cache.get(cache_key)

            if cached:
                logger.info("Live locations cache hit")
                return cached

            queryset = RiderLocation.objects.select_related(
                "rider__user",
                "guest_rider__user"
            ).all()

            cache.set(cache_key, queryset, timeout=30)

            logger.info("Live locations cache rebuilt")

            return queryset

        except Exception as exc:
            logger.error(f"get_queryset failed | error={str(exc)}")
            return RiderLocation.objects.none()

    # =====================================================
    # UPDATE LOCATION
    # =====================================================

    @action(detail=False, methods=["post"])
    def update_location(self, request):

        try:
            user = request.user
            data = request.data

            latitude = data.get("latitude")
            longitude = data.get("longitude")

            if latitude is None or longitude is None:
                logger.warning(f"Invalid GPS payload | user_id={user.id}")
                return Response(
                    {"error": "latitude and longitude required"},
                    status=400
                )

            save_location_task.delay(
                user_id=user.id,
                latitude=latitude,
                longitude=longitude,
                speed=data.get("speed", 0),
                heading=data.get("heading")
            )

            cache.delete("live_locations_v1")

            logger.info(f"Location queued | user_id={user.id}")

            return Response({
                "status": "success",
                "message": "Location queued for processing"
            })

        except Exception as exc:
            logger.error(f"update_location failed | error={str(exc)}")

            return Response(
                {"error": "internal server error"},
                status=500
            )


# =========================================================
# SUSPICIOUS EVENTS VIEWSET
# =========================================================

class SuspiciousEventViewSet(viewsets.ModelViewSet):

    serializer_class = SuspiciousEventSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        try:
            cache_key = "suspicious_events_v1"
            cached = cache.get(cache_key)

            if cached:
                logger.info("Suspicious events cache hit")
                return cached

            queryset = SuspiciousEvent.objects.select_related(
                "rider__user",
                "guest_rider__user"
            ).all()

            cache.set(cache_key, queryset, timeout=60)

            logger.info("Suspicious events cache rebuilt")

            return queryset

        except Exception as exc:
            logger.error(f"suspicious get_queryset failed | error={str(exc)}")
            return SuspiciousEvent.objects.none()