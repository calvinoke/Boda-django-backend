from rest_framework.routers import DefaultRouter
from .views import (

    RiderVerificationViewSet,

    VerificationRequestViewSet
)

router = DefaultRouter()

router.register(
    r'verifications',
    RiderVerificationViewSet,
    basename='verifications'
)

router.register(
    r'verification-requests',
    VerificationRequestViewSet,
    basename='verification-requests'
)

urlpatterns = router.urls