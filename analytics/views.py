from django.core.cache import cache
from rest_framework.views import APIView
from rest_framework.response import (Response)
from rest_framework.permissions import (IsAuthenticated)
from rest_framework import viewsets
from .models import AuditLog
from .serializers import (
    AuditLogSerializer
)
from .services import (
    cache_system_stats
)


# =========================================================
# SYSTEM STATS API
# =========================================================

class SystemStatsAPIView(
    APIView
):

    permission_classes = [
        IsAuthenticated
    ]

    def get(
        self,
        request
    ):

        stats = cache.get(
            "system_stats"
        )

        if not stats:

            stats = cache_system_stats()

        return Response(stats)


# =========================================================
# AUDIT LOG VIEWSET
# =========================================================

class AuditLogViewSet(
    viewsets.ReadOnlyModelViewSet
):

    queryset = AuditLog.objects.select_related(
        'user'
    )

    serializer_class = (
        AuditLogSerializer
    )

    permission_classes = [
        IsAuthenticated
    ]