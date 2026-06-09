from rest_framework.routers import DefaultRouter
from .views import SecurityAlertViewSet

router = DefaultRouter()

router.register(r'security-alerts', SecurityAlertViewSet, basename='security-alerts')

urlpatterns = router.urls