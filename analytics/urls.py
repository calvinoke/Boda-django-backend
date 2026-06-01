from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SystemStatsAPIView, AuditLogViewSet

# =========================================================
# ROUTER
# =========================================================
router = DefaultRouter()
router.register(
    r"audit-logs",
    AuditLogViewSet,
    basename="audit-logs"
)

# =========================================================
# URLS (APP LEVEL ONLY)
# =========================================================

urlpatterns = [
    path(
        "system-stats/",
        SystemStatsAPIView.as_view(),
        name="system-stats"
    ),

    path(
        "",
        include(router.urls)
    ),
]