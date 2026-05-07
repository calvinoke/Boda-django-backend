from rest_framework.routers import DefaultRouter
from .views import RiderProfileViewSet

router = DefaultRouter()

router.register(r'riders', RiderProfileViewSet, basename='riders')

urlpatterns = router.urls