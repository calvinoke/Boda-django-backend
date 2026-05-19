# adminpanel/urls.py
from django.urls import path

from rest_framework.routers import (
    DefaultRouter
)

from .views import (

    SystemStatsAPIView,

    AuditLogViewSet
)

router = DefaultRouter()

router.register(
    r'audit-logs',
    AuditLogViewSet,
    basename='audit-logs'
)

urlpatterns = [

    path(
        'system-stats/',
        SystemStatsAPIView.as_view()
    ),
]

urlpatterns += router.urls