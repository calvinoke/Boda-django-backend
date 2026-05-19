from rest_framework.routers import DefaultRouter
from .views import StageViewSet

router = DefaultRouter()

router.register(
    r'stages',
    StageViewSet,
    basename='stages'
)

urlpatterns = router.urls