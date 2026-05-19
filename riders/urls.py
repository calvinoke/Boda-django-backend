from rest_framework.routers import DefaultRouter
from .views import RiderProfileViewSet, RiderDetailsViewSet, GuestRiderViewSet

router = DefaultRouter()

router.register(r'riders', RiderProfileViewSet, basename='riders')
router.register(r'rider-details', RiderDetailsViewSet, basename='rider-details')
router.register(r'guest-riders', GuestRiderViewSet, basename='guest-riders')

urlpatterns = router.urls