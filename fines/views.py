from rest_framework import viewsets

from rest_framework.decorators import action

from rest_framework.response import Response

from rest_framework.permissions import IsAuthenticated

from rest_framework import status

from django.utils import timezone

from .models import (
    Fine,
    FineType
)

from .serializers import (
    FineSerializer,
    FineTypeSerializer
)

from .permissions import (
    CanIssueFine,
    CanViewFines
)

from .tasks import (

    broadcast_fine_alert,

    refresh_fines_cache,

    cache_unpaid_fines_count
)


# =========================================================
# FINE TYPE VIEWSET
# =========================================================

class FineTypeViewSet(viewsets.ModelViewSet):

    queryset = FineType.objects.filter(
        is_active=True
    )

    serializer_class = FineTypeSerializer

    permission_classes = [
        CanIssueFine
    ]

    search_fields = [
        'name'
    ]

    ordering_fields = [
        'name',
        'default_amount'
    ]


# =========================================================
# FINE VIEWSET
# =========================================================

class FineViewSet(viewsets.ModelViewSet):

    queryset = Fine.objects.select_related(

        'issued_by',

        'rider',

        'guest_rider',

        'stage',

        'fine_type'
    ).order_by('-created_at')

    serializer_class = FineSerializer

    permission_classes = [
        IsAuthenticated,
        CanViewFines
    ]

    search_fields = [

        'reason',

        'status',

        'offender_type',

        'payment_reference'
    ]

    filterset_fields = [

        'status',

        'offender_type',

        'fine_type',

        'stage'
    ]

    ordering_fields = [

        'created_at',

        'amount',

        'status'
    ]

    # =====================================================
    # CREATE FINE
    # =====================================================

    def perform_create(self, serializer):

        fine = serializer.save(

            issued_by=self.request.user
        )

        # =================================================
        # BROADCAST LIVE ALERT
        # =================================================

        broadcast_fine_alert.delay(
            fine.id
        )

        # =================================================
        # REFRESH REDIS CACHE
        # =================================================

        if fine.rider:

            refresh_fines_cache.delay(
                fine.rider.user.id
            )

        elif fine.guest_rider:

            refresh_fines_cache.delay(
                fine.guest_rider.user.id
            )

        # =================================================
        # UPDATE GLOBAL COUNTERS
        # =================================================

        cache_unpaid_fines_count.delay()

    # =====================================================
    # UPDATE FINE
    # =====================================================

    def perform_update(self, serializer):

        fine = serializer.save()

        # =================================================
        # REFRESH CACHE
        # =================================================

        if fine.rider:

            refresh_fines_cache.delay(
                fine.rider.user.id
            )

        elif fine.guest_rider:

            refresh_fines_cache.delay(
                fine.guest_rider.user.id
            )

        # =================================================
        # LIVE UPDATE
        # =================================================

        broadcast_fine_alert.delay(
            fine.id
        )

        cache_unpaid_fines_count.delay()

    # =====================================================
    # DELETE FINE
    # =====================================================

    def perform_destroy(self, instance):

        rider_user_id = None

        guest_user_id = None

        if instance.rider:

            rider_user_id = (
                instance.rider.user.id
            )

        if instance.guest_rider:

            guest_user_id = (
                instance.guest_rider.user.id
            )

        instance.delete()

        # =================================================
        # REFRESH CACHE
        # =================================================

        if rider_user_id:

            refresh_fines_cache.delay(
                rider_user_id
            )

        if guest_user_id:

            refresh_fines_cache.delay(
                guest_user_id
            )

        cache_unpaid_fines_count.delay()

    # =====================================================
    # CUSTOM QUERYSET
    # =====================================================

    def get_queryset(self):

        user = self.request.user

        # =================================================
        # MANAGEMENT CAN VIEW ALL
        # =================================================

        if user.role in [

            'super_admin',

            'stage_chairman',

            'stage_secretary',

            'stage_defense'
        ]:

            return self.queryset

        # =================================================
        # RIDER CAN VIEW OWN FINES
        # =================================================

        if user.role == 'rider':

            return self.queryset.filter(
                rider__user=user
            )

        # =================================================
        # GUEST RIDER CAN VIEW OWN FINES
        # =================================================

        if user.role == 'guest_rider':

            return self.queryset.filter(
                guest_rider__user=user
            )

        return Fine.objects.none()

    # =====================================================
    # MARK FINE AS PAID
    # =====================================================

    @action(
        detail=True,
        methods=['post']
    )
    def mark_as_paid(self, request, pk=None):

        fine = self.get_object()

        fine.status = 'paid'

        fine.paid_at = timezone.now()

        fine.payment_reference = request.data.get(
            'payment_reference'
        )

        fine.save()

        # =================================================
        # REFRESH CACHE
        # =================================================

        if fine.rider:

            refresh_fines_cache.delay(
                fine.rider.user.id
            )

        elif fine.guest_rider:

            refresh_fines_cache.delay(
                fine.guest_rider.user.id
            )

        # =================================================
        # LIVE ALERT
        # =================================================

        broadcast_fine_alert.delay(
            fine.id
        )

        cache_unpaid_fines_count.delay()

        return Response({

            "message": "Fine marked as paid",

            "fine_id": fine.id,

            "status": fine.status
        })

    # =====================================================
    # DISPUTE FINE
    # =====================================================

    @action(
        detail=True,
        methods=['post']
    )
    def dispute(self, request, pk=None):

        fine = self.get_object()

        fine.status = 'disputed'

        fine.save()

        broadcast_fine_alert.delay(
            fine.id
        )

        return Response({

            "message": "Fine disputed successfully",

            "fine_id": fine.id,

            "status": fine.status
        })

    # =====================================================
    # CANCEL FINE
    # =====================================================

    @action(
        detail=True,
        methods=['post']
    )
    def cancel(self, request, pk=None):

        fine = self.get_object()

        fine.status = 'cancelled'

        fine.save()

        broadcast_fine_alert.delay(
            fine.id
        )

        cache_unpaid_fines_count.delay()

        return Response({

            "message": "Fine cancelled",

            "fine_id": fine.id,

            "status": fine.status
        })