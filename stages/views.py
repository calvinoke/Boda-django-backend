import logging

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django.core.cache import cache

from .models import Stage
from .serializers import StageSerializer, StageCreateUpdateSerializer
from .tasks import broadcast_stage_update, refresh_stage_cache
from accounts.permissions import IsManagementRole, IsAdminRole

logger = logging.getLogger("stages.views")


class StageViewSet(viewsets.ModelViewSet):

    queryset = Stage.objects.select_related(
        'chairman',
        'secretary',
        'defense'
    )

    # =====================================================
    # QUERYSET FILTERING
    # =====================================================

    def get_queryset(self):

        cached_stages = cache.get("stages_cache")

        if cached_stages:
            logger.info("Using Redis stage cache")

        user = self.request.user

        if (
            user.is_authenticated and
            hasattr(user, 'role') and
            user.role in [
                'super_admin',
                'stage_chairman',
                'stage_secretary',
                'stage_defense'
            ]
        ):
            return Stage.objects.all()

        return Stage.objects.filter(is_active=True)

    # =====================================================
    # SERIALIZER SWITCH
    # =====================================================

    def get_serializer_class(self):

        if self.action in ['create', 'update', 'partial_update']:
            return StageCreateUpdateSerializer

        return StageSerializer

    # =====================================================
    # PERMISSIONS
    # =====================================================

    def get_permissions(self):

        if self.action == 'destroy':
            return [IsAdminRole()]

        if self.action in ['create', 'update', 'partial_update']:
            return [IsManagementRole()]

        return [IsAuthenticated()]

    # =====================================================
    # INTERNAL HELPER (DRY MESSAGE BUILDER)
    # =====================================================

    def _build_message(self, event, stage):

        return {
            "event": event,
            "stage_id": stage.id,
            "name": stage.name,
        }

    # =====================================================
    # CREATE
    # =====================================================

    def perform_create(self, serializer):

        try:
            stage = serializer.save()

            message = self._build_message("stage_created", stage)

            broadcast_stage_update.delay(message)
            refresh_stage_cache.delay()

            logger.info(f"Stage created | id={stage.id} | name={stage.name}")

        except Exception as exc:
            logger.exception(f"Stage create failed | error={str(exc)}")
            raise

    # =====================================================
    # UPDATE
    # =====================================================

    def perform_update(self, serializer):

        try:
            stage = serializer.save()

            message = self._build_message("stage_updated", stage)

            broadcast_stage_update.delay(message)
            refresh_stage_cache.delay()

            logger.info(f"Stage updated | id={stage.id} | name={stage.name}")

        except Exception as exc:
            logger.exception(f"Stage update failed | error={str(exc)}")
            raise

    # =====================================================
    # DELETE
    # =====================================================

    def perform_destroy(self, instance):

        try:
            stage_id = instance.id
            stage_name = instance.name

            instance.delete()

            message = {
                "event": "stage_deleted",
                "stage_id": stage_id,
                "name": stage_name,
            }

            broadcast_stage_update.delay(message)
            refresh_stage_cache.delay()

            logger.info(f"Stage deleted | id={stage_id} | name={stage_name}")

        except Exception as exc:
            logger.exception(f"Stage delete failed | error={str(exc)}")
            raise