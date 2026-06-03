import logging

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.utils import timezone
from django.core.cache import cache

from .models import RiderVerification, VerificationRequest
from .serializers import (RiderVerificationSerializer,VerificationRequestSerializer)
from .tasks import (broadcast_verification_event,refresh_verification_cache)

logger = logging.getLogger("verification.views")


# =========================================================
# RIDER VERIFICATION VIEWSET
# =========================================================

class RiderVerificationViewSet(viewsets.ModelViewSet):

    serializer_class = RiderVerificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        cached_data = cache.get("verification_cache")

        if cached_data:
            logger.info("Using Redis cache for verification list")

        return RiderVerification.objects.select_related(
            'rider',
            'verified_by'
        ).all()

    def perform_create(self, serializer):

        try:
            verification = serializer.save(
                rider=self.request.user.rider_profile
            )

            logger.info(
                "Verification submitted | verification_id=%s | user=%s",
                verification.id,
                verification.rider.user.username
            )

            broadcast_verification_event.delay({
                "event": "verification_submitted",
                "verification_id": verification.id,
                "username": verification.rider.user.username,
            })

            refresh_verification_cache.delay()

        except Exception as e:
            logger.exception(
                "Failed to create verification | user_id=%s | error=%s",
                self.request.user.id,
                str(e)
            )
            raise


# =========================================================
# VERIFICATION REQUEST VIEWSET
# =========================================================

class VerificationRequestViewSet(viewsets.ModelViewSet):

    serializer_class = VerificationRequestSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    queryset = VerificationRequest.objects.select_related(
        'user',
        'submitted_by'
    ).all()

    def perform_create(self, serializer):

        try:
            request_obj = serializer.save(
                submitted_by=self.request.user
            )

            logger.info(
                "Verification request created | request_id=%s | user_id=%s",
                request_obj.id,
                request_obj.user_id
            )

            broadcast_verification_event.delay({
                "event": "verification_request_created",
                "request_id": request_obj.id,
                "username": request_obj.user.username,
            })

            refresh_verification_cache.delay()

        except Exception as e:
            logger.exception(
                "Failed to create verification request | admin_id=%s | error=%s",
                self.request.user.id,
                str(e)
            )
            raise

    def perform_update(self, serializer):

        try:
            instance = serializer.save()

            # =================================================
            # APPROVED
            # =================================================

            if instance.status == "approved":

                RiderVerification.objects.filter(
                    rider__user=instance.user
                ).update(
                    is_verified=True,
                    verified_by=self.request.user,
                    verified_at=timezone.now()
                )

                logger.info(
                    "Verification approved | user_id=%s | admin_id=%s",
                    instance.user_id,
                    self.request.user.id
                )

                broadcast_verification_event.delay({
                    "event": "verification_approved",
                    "user_id": instance.user.id,
                    "username": instance.user.username,
                })

            # =================================================
            # REJECTED
            # =================================================

            elif instance.status == "rejected":

                logger.info(
                    "Verification rejected | user_id=%s | admin_id=%s",
                    instance.user_id,
                    self.request.user.id
                )

                broadcast_verification_event.delay({
                    "event": "verification_rejected",
                    "user_id": instance.user.id,
                    "username": instance.user.username,
                })

            refresh_verification_cache.delay()

        except Exception as e:
            logger.exception(
                "Failed to update verification request | request_id=%s | error=%s",
                instance.id if 'instance' in locals() else None,
                str(e)
            )
            raise