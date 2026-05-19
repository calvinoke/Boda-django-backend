from rest_framework.routers import (DefaultRouter)
from .views import (EmergencyContactViewSet)

router = DefaultRouter()

router.register(

    r'contacts',

    EmergencyContactViewSet,

    basename='contacts'
)

urlpatterns = router.urls