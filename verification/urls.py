from rest_framework.routers import DefaultRouter
from .views import RiderVerificationViewSet

router = DefaultRouter()

router.register(
    r'verifications',
    RiderVerificationViewSet,
    basename='verifications'
)

urlpatterns = router.urls