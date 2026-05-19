from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django.core.cache import cache
from .models import Stage
from .serializers import (

    StageSerializer,

    StageCreateUpdateSerializer
)
from .tasks import (

    broadcast_stage_update,

    refresh_stage_cache
)
from accounts.permissions import (

    IsManagementRole,

    IsAdminRole
)


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
            print("Using Redis stage cache")

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

        return Stage.objects.filter(
            is_active=True
        )

    # =====================================================
    # SERIALIZER SWITCH
    # =====================================================

    def get_serializer_class(self):

        if self.action in [

            'create',

            'update',

            'partial_update'
        ]:
            return StageCreateUpdateSerializer

        return StageSerializer

    # =====================================================
    # PERMISSIONS
    # =====================================================

    def get_permissions(self):

        if self.action == 'destroy':
            return [IsAdminRole()]

        if self.action in [

            'create',

            'update',

            'partial_update'
        ]:
            return [IsManagementRole()]

        return [IsAuthenticated()]

    # =====================================================
    # CREATE
    # =====================================================

    def perform_create(self, serializer):

        stage = serializer.save()

        message = {

            "event": "stage_created",

            "stage_id": stage.id,

            "name": stage.name,
        }

        broadcast_stage_update.delay(message)

        refresh_stage_cache.delay()

    # =====================================================
    # UPDATE
    # =====================================================

    def perform_update(self, serializer):

        stage = serializer.save()

        message = {

            "event": "stage_updated",

            "stage_id": stage.id,

            "name": stage.name,
        }

        broadcast_stage_update.delay(message)

        refresh_stage_cache.delay()

    # =====================================================
    # DELETE
    # =====================================================

    def perform_destroy(self, instance):

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