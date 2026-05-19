from rest_framework.routers import DefaultRouter

from .views import (
    LocationViewSet,
    SuspiciousEventViewSet
)

router = DefaultRouter()

router.register(
    r'location',
    LocationViewSet,
    basename='location'
)

router.register(
    r'suspicious-events',
    SuspiciousEventViewSet,
    basename='suspicious-events'
)

urlpatterns = router.urls