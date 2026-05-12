from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Stage
from .serializers import (
    StageSerializer,
    StageCreateUpdateSerializer
)

from accounts.permissions import (
    IsManagementRole,
    IsAdminRole
)


# =========================================================
# STAGE VIEWSET
# =========================================================

class StageViewSet(viewsets.ModelViewSet):

    queryset = Stage.objects.select_related(
        'chairman',
        'secretary',
        'defense'
    ).all()

    # =====================================================
    # QUERYSET SECURITY
    # =====================================================

    def get_queryset(self):

        user = self.request.user

        # MANAGEMENT CAN SEE ALL STAGES
        if user.role in [
            'super_admin',
            'stage_chairman',
            'stage_secretary',
            'stage_defense'
        ]:
            return Stage.objects.all()

        # RIDERS CAN ONLY SEE ACTIVE STAGES
        return Stage.objects.filter(is_active=True)

    # =====================================================
    # SERIALIZER CONTROL
    # =====================================================

    def get_serializer_class(self):

        # ONLY MANAGEMENT CAN CREATE/UPDATE FULL STAGE
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return StageCreateUpdateSerializer

        return StageSerializer

    # =====================================================
    # PERMISSIONS
    # =====================================================

    def get_permissions(self):

        # ONLY SUPER ADMIN CAN DELETE
        if self.action == 'destroy':
            return [IsAdminRole()]

        # ALL MANAGEMENT CAN CREATE/UPDATE
        if self.action in ['create', 'update', 'partial_update']:
            return [IsManagementRole()]

        # EVERYONE CAN VIEW (BUT FILTERED IN QUERYSET)
        return [IsAuthenticated()]