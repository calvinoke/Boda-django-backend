import logging
from django.core.cache import cache
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from .models import AuditLog
from .serializers import AuditLogSerializer
from .services import cache_system_stats


# =========================================================
# LOGGER
# =========================================================

logger = logging.getLogger(__name__)


# =========================================================
# SYSTEM STATS API (PRODUCTION READY)
# =========================================================

class SystemStatsAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        try:

            logger.info(f"System stats requested by user: {request.user.id}")

            stats = cache.get("system_stats")

            if stats:
                logger.info("System stats cache HIT")
                return Response(stats)

            logger.warning("System stats cache MISS - recomputing")

            stats = cache_system_stats()

            return Response(stats)

        except Exception as e:

            logger.error(
                f"SystemStatsAPIView failed: {str(e)}",
                exc_info=True
            )

            return Response(
                {
                    "error": "Unable to load system stats"
                },
                status=500
            )


# =========================================================
# PAGINATION (IMPORTANT FOR PRODUCTION)
# =========================================================

class AuditLogPagination(PageNumberPagination):
    page_size = 50
    max_page_size = 200


# =========================================================
# AUDIT LOG VIEWSET (PRODUCTION READY)
# =========================================================

class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = AuditLog.objects.select_related('user')

    serializer_class = AuditLogSerializer

    permission_classes = [IsAuthenticated]

    pagination_class = AuditLogPagination

    def list(self, request, *args, **kwargs):

        logger.info(f"Audit logs accessed by user: {request.user.id}")

        return super().list(request, *args, **kwargs)