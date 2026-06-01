import logging
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Announcement, Condolence
from .serializers import AnnouncementSerializer, CondolenceSerializer


# =========================================================
# LOGGER
# =========================================================

logger = logging.getLogger("api")


# =========================================================
# ANNOUNCEMENT VIEWSET
# =========================================================

class AnnouncementViewSet(viewsets.ModelViewSet):

    serializer_class = AnnouncementSerializer
    permission_classes = [IsAuthenticated]

    queryset = Announcement.objects.select_related("created_by")

    # =====================================================
    # CREATE ANNOUNCEMENT (AUDITED)
    # =====================================================

    def perform_create(self, serializer):

        user = self.request.user

        try:
            instance = serializer.save(created_by=user)

            logger.info(
                f"Announcement created | id={instance.id} | user={user.id}"
            )

        except Exception as exc:

            logger.error(
                f"Announcement create failed | user={user.id} | error={str(exc)}"
            )

            raise


# =========================================================
# CONDOLENCE VIEWSET
# =========================================================

class CondolenceViewSet(viewsets.ModelViewSet):

    serializer_class = CondolenceSerializer
    permission_classes = [IsAuthenticated]

    queryset = Condolence.objects.select_related(
        "rider",
        "reported_by",
        "verified_by",
    )

    # =====================================================
    # CREATE CONDOLENCE (AUDITED)
    # =====================================================

    def perform_create(self, serializer):

        user = self.request.user

        try:
            instance = serializer.save(reported_by=user)

            logger.info(
                f"Condolence created | id={instance.id} | user={user.id}"
            )

        except Exception as exc:

            logger.error(
                f"Condolence create failed | user={user.id} | error={str(exc)}"
            )

            raise