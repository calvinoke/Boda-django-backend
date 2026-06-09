from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AnnouncementViewSet, CondolenceViewSet

router = DefaultRouter()

router.register(r"announcements", AnnouncementViewSet, basename="announcements")
router.register(r"condolences", CondolenceViewSet, basename="condolences")

urlpatterns = [
    path("", include(router.urls)),
]