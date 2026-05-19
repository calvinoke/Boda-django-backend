from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import SecurityAlert
from .serializers import (
    SecurityAlertSerializer
)

from .tasks import (

    broadcast_security_alert,

    refresh_security_alert_cache
)


class SecurityAlertViewSet(

    viewsets.ModelViewSet
):

    serializer_class = SecurityAlertSerializer

    permission_classes = [IsAuthenticated]

    queryset = SecurityAlert.objects.select_related(
        'user',
        'resolved_by'
    )

    # =====================================================
    # QUERYSET FILTERING
    # =====================================================

    def get_queryset(self):

        user = self.request.user

        if user.is_staff or (

            hasattr(user, 'role') and

            user.role == 'super_admin'
        ):

            return self.queryset.all()

        return self.queryset.filter(
            user=user
        )

    # =====================================================
    # CREATE ALERT
    # =====================================================

    def perform_create(self, serializer):

        alert = serializer.save(

            user=self.request.user
        )

        # =================================================
        # CELERY TASKS
        # =================================================

        broadcast_security_alert.delay(
            alert.id
        )

        refresh_security_alert_cache.delay()

    # =====================================================
    # RESOLVE ALERT
    # =====================================================

    @action(

        detail=True,

        methods=['post']
    )
    def resolve_alert(

        self,
        request,
        pk=None
    ):

        alert = self.get_object()

        alert.resolved = True

        alert.resolved_by = request.user

        alert.resolved_at = timezone