import logging
from django.db import transaction
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from riders.models import RiderProfile
from accounts.permissions import IsAdminRole
from .models import (RiderActivity,SystemLog)
from .tasks import (broadcast_admin_event,refresh_admin_cache)

# =========================================================
# LOGGER
# =========================================================

logger = logging.getLogger(__name__)


# =========================================================
# APPROVE RIDER
# =========================================================

class ApproveRiderAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdminRole
    ]

    @transaction.atomic
    def post(self, request, rider_id):

        try:

            rider = RiderProfile.objects.select_related(
                "user"
            ).get(
                id=rider_id
            )

            if rider.status == "approved":

                logger.warning(
                    f"Rider already approved: {rider.id}"
                )

                return Response(
                    {
                        "error":
                        "Rider is already approved"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            rider.status = "approved"
            rider.save(
                update_fields=["status"]
            )

            RiderActivity.objects.create(
                rider=rider,
                action="approved",
                description=(
                    f"Approved by "
                    f"{request.user.email}"
                )
            )

            SystemLog.objects.create(
                level="info",
                message=(
                    f"Rider "
                    f"{rider.user.email} "
                    f"approved by "
                    f"{request.user.email}"
                )
            )

            broadcast_admin_event.delay(
                f"Rider {rider.user.email} approved"
            )

            refresh_admin_cache.delay()

            logger.info(
                f"Rider approved successfully: "
                f"{rider.user.email}"
            )

            return Response(
                {
                    "message":
                    "Rider approved successfully"
                },
                status=status.HTTP_200_OK
            )

        except RiderProfile.DoesNotExist:

            logger.warning(
                f"Rider not found: {rider_id}"
            )

            return Response(
                {
                    "error":
                    "Rider not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        except Exception as exc:

            logger.exception(
                f"Approve rider failed: {str(exc)}"
            )

            return Response(
                {
                    "error":
                    "Internal server error"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# =========================================================
# SUSPEND RIDER
# =========================================================

class SuspendRiderAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdminRole
    ]

    @transaction.atomic
    def post(self, request, rider_id):

        try:

            rider = RiderProfile.objects.select_related(
                "user"
            ).get(
                id=rider_id
            )

            if rider.status == "suspended":

                logger.warning(
                    f"Rider already suspended: "
                    f"{rider.id}"
                )

                return Response(
                    {
                        "error":
                        "Rider is already suspended"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            rider.status = "suspended"

            rider.save(
                update_fields=["status"]
            )

            RiderActivity.objects.create(
                rider=rider,
                action="suspended",
                description=(
                    f"Suspended by "
                    f"{request.user.email}"
                )
            )

            SystemLog.objects.create(
                level="warning",
                message=(
                    f"Rider "
                    f"{rider.user.email} "
                    f"suspended by "
                    f"{request.user.email}"
                )
            )

            broadcast_admin_event.delay(
                f"Rider {rider.user.email} suspended"
            )

            refresh_admin_cache.delay()

            logger.warning(
                f"Rider suspended: "
                f"{rider.user.email}"
            )

            return Response(
                {
                    "message":
                    "Rider suspended successfully"
                },
                status=status.HTTP_200_OK
            )

        except RiderProfile.DoesNotExist:

            logger.warning(
                f"Rider not found: {rider_id}"
            )

            return Response(
                {
                    "error":
                    "Rider not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        except Exception as exc:

            logger.exception(
                f"Suspend rider failed: {str(exc)}"
            )

            return Response(
                {
                    "error":
                    "Internal server error"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )