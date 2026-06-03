import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import Fine, FineType
from .serializers import FineSerializer, FineTypeSerializer
from .permissions import CanIssueFine, CanViewFines
from .tasks import (
    broadcast_fine_alert,
    refresh_fines_cache,
    cache_unpaid_fines_count
)

# =========================================================
# LOGGER
# =========================================================

logger = logging.getLogger("fines.views")


# =========================================================
# FINE TYPE VIEWSET
# =========================================================

class FineTypeViewSet(viewsets.ModelViewSet):

    queryset = FineType.objects.filter(is_active=True)
    serializer_class = FineTypeSerializer
    permission_classes = [CanIssueFine]

    search_fields = ["name"]
    ordering_fields = ["name", "default_amount"]

    def perform_create(self, serializer):
        obj = serializer.save()

        logger.info(
            f"FineType created | id={obj.id} | user={self.request.user.id}"
        )


# =========================================================
# FINE VIEWSET
# =========================================================

class FineViewSet(viewsets.ModelViewSet):

    queryset = Fine.objects.select_related(
        "issued_by",
        "rider",
        "guest_rider",
        "stage",
        "fine_type"
    ).order_by("-created_at")

    serializer_class = FineSerializer
    permission_classes = [IsAuthenticated, CanViewFines]

    search_fields = ["reason", "status", "offender_type", "payment_reference"]

    filterset_fields = ["status", "offender_type", "fine_type", "stage"]

    ordering_fields = ["created_at", "amount", "status"]

    # =====================================================
    # CREATE
    # =====================================================

    def perform_create(self, serializer):

        try:
            fine = serializer.save(issued_by=self.request.user)

            logger.info(
                f"Fine created | fine_id={fine.id} | user_id={self.request.user.id}"
            )

            broadcast_fine_alert.delay(fine.id)
            cache_unpaid_fines_count.delay()

            user_id = fine.rider.user.id if fine.rider else (
                fine.guest_rider.user.id if fine.guest_rider else None
            )

            if user_id:
                refresh_fines_cache.delay(user_id)

        except Exception as exc:
            logger.error(
                f"Fine creation failed | user_id={self.request.user.id} | error={str(exc)}"
            )
            raise

    # =====================================================
    # UPDATE
    # =====================================================

    def perform_update(self, serializer):

        try:
            fine = serializer.save()

            logger.info(
                f"Fine updated | fine_id={fine.id}"
            )

            broadcast_fine_alert.delay(fine.id)
            cache_unpaid_fines_count.delay()

            user_id = fine.rider.user.id if fine.rider else (
                fine.guest_rider.user.id if fine.guest_rider else None
            )

            if user_id:
                refresh_fines_cache.delay(user_id)

        except Exception as exc:
            logger.error(
                f"Fine update failed | error={str(exc)}"
            )
            raise

    # =====================================================
    # DELETE
    # =====================================================

    def perform_destroy(self, instance):

        try:
            fine_id = instance.id

            user_id = instance.rider.user.id if instance.rider else (
                instance.guest_rider.user.id if instance.guest_rider else None
            )

            instance.delete()

            logger.info(
                f"Fine deleted | fine_id={fine_id}"
            )

            if user_id:
                refresh_fines_cache.delay(user_id)

            cache_unpaid_fines_count.delay()
            broadcast_fine_alert.delay(fine_id)

        except Exception as exc:
            logger.error(
                f"Fine delete failed | error={str(exc)}"
            )
            raise

    # =====================================================
    # QUERYSET (ROLE BASED ACCESS)
    # =====================================================

    def get_queryset(self):

        user = self.request.user

        try:
            if user.role in [
                "super_admin",
                "stage_chairman",
                "stage_secretary",
                "stage_defense"
            ]:
                return self.queryset

            if user.role == "rider":
                return self.queryset.filter(rider__user=user)

            if user.role == "guest_rider":
                return self.queryset.filter(guest_rider__user=user)

            return Fine.objects.none()

        except Exception as exc:
            logger.error(
                f"Queryset error | user_id={user.id} | error={str(exc)}"
            )
            return Fine.objects.none()

    # =====================================================
    # MARK AS PAID
    # =====================================================

    @action(detail=True, methods=["post"])
    def mark_as_paid(self, request, pk=None):

        fine = self.get_object()

        if fine.status == "paid":
            return Response(
                {"detail": "Fine already paid"},
                status=status.HTTP_400_BAD_REQUEST
            )

        fine.status = "paid"
        fine.paid_at = timezone.now()
        fine.payment_reference = request.data.get("payment_reference", "")
        fine.save()

        logger.info(f"Fine marked paid | fine_id={fine.id}")

        broadcast_fine_alert.delay(fine.id)
        cache_unpaid_fines_count.delay()

        return Response({
            "message": "Fine marked as paid",
            "fine_id": fine.id,
            "status": fine.status
        })

    # =====================================================
    # DISPUTE
    # =====================================================

    @action(detail=True, methods=["post"])
    def dispute(self, request, pk=None):

        fine = self.get_object()

        if fine.status in ["paid", "cancelled"]:
            return Response(
                {"detail": "Cannot dispute this fine"},
                status=status.HTTP_400_BAD_REQUEST
            )

        fine.status = "disputed"
        fine.save()

        logger.info(f"Fine disputed | fine_id={fine.id}")

        broadcast_fine_alert.delay(fine.id)

        return Response({
            "message": "Fine disputed successfully",
            "fine_id": fine.id,
            "status": fine.status
        })

    # =====================================================
    # CANCEL
    # =====================================================

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):

        fine = self.get_object()

        if fine.status == "paid":
            return Response(
                {"detail": "Cannot cancel a paid fine"},
                status=status.HTTP_400_BAD_REQUEST
            )

        fine.status = "cancelled"
        fine.save()

        logger.info(f"Fine cancelled | fine_id={fine.id}")

        broadcast_fine_alert.delay(fine.id)
        cache_unpaid_fines_count.delay()

        return Response({
            "message": "Fine cancelled",
            "fine_id": fine.id,
            "status": fine.status
        })