from rest_framework.routers import DefaultRouter
from .views import FineViewSet, FineTypeViewSet

router = DefaultRouter()

router.register(r'fines', FineViewSet, basename='fines')
router.register(r'fine-types', FineTypeViewSet, basename='fine-types')

urlpatterns = router.urls