from rest_framework import viewsets
from rest_framework.permissions import (

    IsAuthenticated,

    IsAdminUser
)
from django.utils import timezone
from django.core.cache import cache
from .models import (

    RiderVerification,

    VerificationRequest
)
from .serializers import (

    RiderVerificationSerializer,

    VerificationRequestSerializer
)
from .tasks import (

    broadcast_verification_event,

    refresh_verification_cache
)


# =========================================================
# RIDER VERIFICATION VIEWSET
# =========================================================

class RiderVerificationViewSet(

    viewsets.ModelViewSet
):

    serializer_class = RiderVerificationSerializer

    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        cached_data = cache.get(
            "verification_cache"
        )

        if cached_data:
            print("Using Redis cache")

        return RiderVerification.objects.select_related(

            'rider',

            'verified_by'
        ).all()

    def perform_create(
        self,
        serializer
    ):

        verification = serializer.save(

            rider=self.request.user.rider_profile
        )

        # =================================================
        # CELERY TASKS
        # =================================================

        broadcast_verification_event.delay({

            "event": "verification_submitted",

            "verification_id": verification.id,

            "username": verification.rider.user.username,
        })

        refresh_verification_cache.delay()


# =========================================================
# VERIFICATION REQUEST VIEWSET
# =========================================================

class VerificationRequestViewSet(

    viewsets.ModelViewSet
):

    serializer_class = VerificationRequestSerializer

    permission_classes = [

        IsAuthenticated,

        IsAdminUser
    ]

    queryset = VerificationRequest.objects.select_related(

        'user',

        'submitted_by'
    ).all()

    def perform_create(
        self,
        serializer
    ):

        request_obj = serializer.save(

            submitted_by=self.request.user
        )

        broadcast_verification_event.delay({

            "event": "verification_request_created",

            "request_id": request_obj.id,

            "username": request_obj.user.username,
        })

        refresh_verification_cache.delay()

    def perform_update(
        self,
        serializer
    ):

        instance = serializer.save()

        # =================================================
        # APPROVE VERIFICATION
        # =================================================

        if instance.status == "approved":

            RiderVerification.objects.filter(

                rider__user=instance.user

            ).update(

                is_verified=True,

                verified_by=self.request.user,

                verified_at=timezone.now()
            )

            broadcast_verification_event.delay({

                "event": "verification_approved",

                "user_id": instance.user.id,

                "username": instance.user.username,
            })

        # =================================================
        # REJECT VERIFICATION
        # =================================================

        elif instance.status == "rejected":

            broadcast_verification_event.delay({

                "event": "verification_rejected",

                "user_id": instance.user.id,

                "username": instance.user.username,
            })

        refresh_verification_cache.delay()