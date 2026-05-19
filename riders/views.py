from django.core.cache import cache

from rest_framework import viewsets

from rest_framework.permissions import (
    IsAuthenticated
)

from rest_framework.decorators import action

from rest_framework.response import Response

from .models import (
    RiderProfile,
    RiderDetails,
    GuestRider
)

from .serializers import (

    RiderProfileSerializer,

    RiderDetailsSerializer,

    GuestRiderSerializer
)

from .tasks import (

    refresh_riders_cache,

    refresh_guest_riders_cache,

    set_rider_online_status
)


# =========================================================
# RIDER PROFILE VIEWSET
# =========================================================

class RiderProfileViewSet(
    viewsets.ModelViewSet
):

    serializer_class = (
        RiderProfileSerializer
    )

    permission_classes = [
        IsAuthenticated
    ]

    def get_queryset(self):

        user = self.request.user

        if user.role in [

            'super_admin',

            'stage_chairman',

            'stage_secretary',

            'stage_defense'
        ]:

            return RiderProfile.objects.all()

        return RiderProfile.objects.filter(
            user=user
        )

    # =====================================================
    # ONLINE STATUS
    # =====================================================

    @action(
        detail=True,
        methods=['post']
    )
    def set_online(
        self,
        request,
        pk=None
    ):

        set_rider_online_status.delay(
            pk,
            True
        )

        return Response({

            "message":
            "Rider set online"
        })

    @action(
        detail=True,
        methods=['post']
    )
    def set_offline(
        self,
        request,
        pk=None
    ):

        set_rider_online_status.delay(
            pk,
            False
        )

        return Response({

            "message":
            "Rider set offline"
        })

    # =====================================================
    # CACHED RIDERS
    # =====================================================

    @action(
        detail=False,
        methods=['get']
    )
    def cached(
        self,
        request
    ):

        data = cache.get(
            "active_riders"
        )

        if not data:

            refresh_riders_cache.delay()

            return Response({

                "message":
                "Cache rebuilding"
            })

        return Response(data)


# =========================================================
# RIDER DETAILS VIEWSET
# =========================================================

class RiderDetailsViewSet(
    viewsets.ModelViewSet
):

    serializer_class = (
        RiderDetailsSerializer
    )

    queryset = RiderDetails.objects.all()

    permission_classes = [
        IsAuthenticated
    ]

    def perform_create(
        self,
        serializer
    ):

        serializer.save(
            rider=self.request.user.rider_profile
        )

    def get_queryset(self):

        user = self.request.user

        if user.role in [

            'super_admin',

            'stage_chairman',

            'stage_secretary',

            'stage_defense'
        ]:

            return self.queryset

        return self.queryset.filter(
            rider__user=user
        )


# =========================================================
# GUEST RIDER VIEWSET
# =========================================================

class GuestRiderViewSet(
    viewsets.ModelViewSet
):

    serializer_class = (
        GuestRiderSerializer
    )

    permission_classes = [
        IsAuthenticated
    ]

    def get_queryset(self):

        user = self.request.user

        if user.role in [

            'super_admin',

            'stage_chairman',

            'stage_secretary',

            'stage_defense'
        ]:

            return GuestRider.objects.all()

        return GuestRider.objects.filter(
            user=user
        )

    @action(
        detail=False,
        methods=['get']
    )
    def cached(
        self,
        request
    ):

        data = cache.get(
            "guest_riders"
        )

        if not data:

            refresh_guest_riders_cache.delay()

            return Response({

                "message":
                "Cache rebuilding"
            })

        return Response(data)