import logging
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from django.core.cache import cache
from .models import EmergencyContact
from .serializers import EmergencyContactSerializer
from .tasks import refresh_contact_cache


# =========================================================
# LOGGER
# =========================================================

logger = logging.getLogger("api")


CACHE_KEY_PREFIX = "v1_rider_contacts"


# =========================================================
# VIEWSET
# =========================================================

class EmergencyContactViewSet(viewsets.ModelViewSet):

    serializer_class = EmergencyContactSerializer
    permission_classes = [IsAuthenticated]

    search_fields = ["name", "phone_number", "relationship"]
    ordering_fields = ["created_at"]

    # =====================================================
    # QUERYSET (SAFE + PRODUCTION READY)
    # =====================================================

    def get_queryset(self):

        user = self.request.user

        try:
            queryset = EmergencyContact.objects.select_related(
                "rider",
                "rider__user"
            ).filter(
                rider__user=user
            )

            logger.info(f"Queryset loaded | user_id={user.id}")

            return queryset

        except Exception as exc:

            logger.error(
                f"Queryset error | user_id={user.id} | error={str(exc)}"
            )

            return EmergencyContact.objects.none()

    # =====================================================
    # CREATE
    # =====================================================

    def perform_create(self, serializer):

        user = self.request.user

        try:
            rider_profile = getattr(user, "rider_profile", None)

            if not rider_profile:
                logger.warning(
                    f"Create blocked (missing rider_profile) | user_id={user.id}"
                )
                raise ValueError("Rider profile missing")

            contact = serializer.save(rider=rider_profile)

            logger.info(
                f"Contact created | contact_id={contact.id} | user_id={user.id}"
            )

            refresh_contact_cache.delay(user.id)

            logger.info(
                f"Cache refresh triggered (create) | user_id={user.id}"
            )

        except Exception as exc:

            logger.error(
                f"Contact create failed | user_id={user.id} | error={str(exc)}"
            )

            raise

    # =====================================================
    # UPDATE
    # =====================================================

    def perform_update(self, serializer):

        user = self.request.user

        try:
            contact = serializer.save()

            logger.info(
                f"Contact updated | contact_id={contact.id} | user_id={user.id}"
            )

            refresh_contact_cache.delay(user.id)

            logger.info(
                f"Cache refresh triggered (update) | user_id={user.id}"
            )

        except Exception as exc:

            logger.error(
                f"Contact update failed | user_id={user.id} | error={str(exc)}"
            )

            raise

    # =====================================================
    # DELETE
    # =====================================================

    def perform_destroy(self, instance):

        user = self.request.user

        try:
            contact_id = instance.id
            instance.delete()

            logger.info(
                f"Contact deleted | contact_id={contact_id} | user_id={user.id}"
            )

            refresh_contact_cache.delay(user.id)

            logger.info(
                f"Cache refresh triggered (delete) | user_id={user.id}"
            )

        except Exception as exc:

            logger.error(
                f"Contact delete failed | contact_id={instance.id} | user_id={user.id} | error={str(exc)}"
            )

            raise

    # =====================================================
    # CACHED CONTACTS ENDPOINT
    # =====================================================

    @action(detail=False, methods=["get"])
    def cached_contacts(self, request):

        user = request.user

        cache_key = f"{CACHE_KEY_PREFIX}_{user.id}"

        try:
            data = cache.get(cache_key)

            logger.info(f"Cache accessed | user_id={user.id}")

            return Response(
                {
                    "cached": True,
                    "data": data or []
                }
            )

        except Exception as exc:

            logger.error(
                f"Cache fetch failed | user_id={user.id} | error={str(exc)}"
            )

            return Response(
                {
                    "cached": False,
                    "data": []
                }
            )