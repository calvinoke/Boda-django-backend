import logging
from django.core.cache import cache
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import RiderProfile, RiderDetails, GuestRider
from .serializers import (RiderProfileSerializer,RiderDetailsSerializer,GuestRiderSerializer)
from .tasks import (refresh_riders_cache,refresh_guest_riders_cache,set_rider_online_status)

logger = logging.getLogger("riders.views")


# =========================================================
# RIDER PROFILE VIEWSET
# =========================================================

class RiderProfileViewSet(viewsets.ModelViewSet):

    serializer_class = RiderProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        user = self.request.user

        try:
            if user.role in [
                'super_admin',
                'stage_chairman',
                'stage_secretary',
                'stage_defense'
            ]:
                qs = RiderProfile.objects.all()
            else:
                qs = RiderProfile.objects.filter(user=user)

            logger.info(f"RiderProfile queryset loaded | user_id={user.id}")
            return qs

        except Exception as exc:
            logger.error(f"RiderProfile queryset error | user_id={user.id} | error={str(exc)}")
            return RiderProfile.objects.none()

    # =====================================================
    # ONLINE STATUS
    # =====================================================

    @action(detail=True, methods=['post'])
    def set_online(self, request, pk=None):

        try:
            set_rider_online_status.delay(pk, True)

            logger.info(f"Set rider online triggered | rider_id={pk}")

            return Response({"message": "Rider set online"})

        except Exception as exc:
            logger.error(f"Set online failed | rider_id={pk} | error={str(exc)}")
            raise

    @action(detail=True, methods=['post'])
    def set_offline(self, request, pk=None):

        try:
            set_rider_online_status.delay(pk, False)

            logger.info(f"Set rider offline triggered | rider_id={pk}")

            return Response({"message": "Rider set offline"})

        except Exception as exc:
            logger.error(f"Set offline failed | rider_id={pk} | error={str(exc)}")
            raise

    # =====================================================
    # CACHED RIDERS
    # =====================================================

    @action(detail=False, methods=['get'])
    def cached(self, request):

        try:
            data = cache.get("active_riders")

            if not data:
                refresh_riders_cache.delay()

                logger.warning("Active riders cache miss - rebuild triggered")

                return Response({"message": "Cache rebuilding"})

            logger.info("Active riders cache hit")
            return Response(data)

        except Exception as exc:
            logger.error(f"Cached riders error | error={str(exc)}")
            return Response({"message": "Cache error"})


# =========================================================
# RIDER DETAILS VIEWSET
# =========================================================

class RiderDetailsViewSet(viewsets.ModelViewSet):

    serializer_class = RiderDetailsSerializer
    queryset = RiderDetails.objects.all()
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):

        user = self.request.user

        try:
            serializer.save(rider=user.rider_profile)

            logger.info(f"Rider details created | user_id={user.id}")

        except Exception as exc:
            logger.error(f"Rider details create failed | user_id={user.id} | error={str(exc)}")
            raise

    def get_queryset(self):

        user = self.request.user

        try:
            if user.role in [
                'super_admin',
                'stage_chairman',
                'stage_secretary',
                'stage_defense'
            ]:
                return self.queryset

            return self.queryset.filter(rider__user=user)

        except Exception as exc:
            logger.error(f"RiderDetails queryset error | user_id={user.id} | error={str(exc)}")
            return RiderDetails.objects.none()


# =========================================================
# GUEST RIDER VIEWSET
# =========================================================

class GuestRiderViewSet(viewsets.ModelViewSet):

    serializer_class = GuestRiderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        user = self.request.user

        try:
            if user.role in [
                'super_admin',
                'stage_chairman',
                'stage_secretary',
                'stage_defense'
            ]:
                return GuestRider.objects.all()

            return GuestRider.objects.filter(user=user)

        except Exception as exc:
            logger.error(f"GuestRider queryset error | user_id={user.id} | error={str(exc)}")
            return GuestRider.objects.none()

    @action(detail=False, methods=['get'])
    def cached(self, request):

        try:
            data = cache.get("guest_riders")

            if not data:
                refresh_guest_riders_cache.delay()

                logger.warning("Guest riders cache miss - rebuild triggered")

                return Response({"message": "Cache rebuilding"})

            logger.info("Guest riders cache hit")
            return Response(data)

        except Exception as exc:
            logger.error(f"Guest riders cache error | error={str(exc)}")
            return Response({"message": "Cache error"})