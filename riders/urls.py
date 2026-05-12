from rest_framework.routers import DefaultRouter

from .views import (

    RiderProfileViewSet,

    RiderDetailsViewSet,

    GuestRiderViewSet
)

router = DefaultRouter()

# REGISTERED RIDERS
router.register(
    r'riders',
    RiderProfileViewSet,
    basename='riders'
)

# RIDER DETAILS
router.register(
    r'rider-details',
    RiderDetailsViewSet,
    basename='rider-details'
)

# GUEST RIDERS
router.register(
    r'guest-riders',
    GuestRiderViewSet,
    basename='guest-riders'
)

urlpatterns = router.urls