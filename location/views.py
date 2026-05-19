from django.core.cache import cache

from rest_framework import viewsets

from rest_framework.decorators import action

from rest_framework.response import Response

from rest_framework.permissions import IsAuthenticated

from .models import (
    RiderLocation,
    SuspiciousEvent
)

from .serializers import (
    RiderLocationSerializer,
    SuspiciousEventSerializer
)

from .tasks import (
    save_location_task
)


# =========================================================
# LOCATION VIEWSET
# =========================================================

class LocationViewSet(viewsets.ModelViewSet):

    serializer_class = RiderLocationSerializer

    permission_classes = [IsAuthenticated]

    # =====================================================
    # OPTIMIZED QUERYSET
    # =====================================================

    def get_queryset(self):

        queryset = cache.get("live_locations")

        if queryset:

            return queryset

        queryset = RiderLocation.objects.select_related(

            'rider__user',

            'guest_rider__user'
        ).all()

        cache.set(

            "live_locations",

            queryset,

            timeout=30
        )

        return queryset

    # =====================================================
    # LIVE LOCATION UPDATE
    # =====================================================

    @action(
        detail=False,
        methods=['post']
    )
    def update_location(self, request):

        user = request.user

        data = request.data

        # =================================================
        # SEND TO CELERY
        # =================================================

        save_location_task.delay(

            user_id=user.id,

            latitude=data.get('latitude'),

            longitude=data.get('longitude'),

            speed=data.get('speed', 0),

            heading=data.get('heading')
        )

        # CLEAR CACHE
        cache.delete("live_locations")

        return Response({

            "status": "success",

            "message": "Location queued for processing"
        })


# =========================================================
# SUSPICIOUS EVENTS VIEWSET
# =========================================================

class SuspiciousEventViewSet(viewsets.ModelViewSet):

    serializer_class = SuspiciousEventSerializer

    permission_classes = [IsAuthenticated]

    # =====================================================
    # OPTIMIZED QUERYSET
    # =====================================================

    def get_queryset(self):

        queryset = cache.get("suspicious_events")

        if queryset:

            return queryset

        queryset = SuspiciousEvent.objects.select_related(

            'rider__user',

            'guest_rider__user'
        ).all()

        cache.set(

            "suspicious_events",

            queryset,

            timeout=60
        )

        return queryset