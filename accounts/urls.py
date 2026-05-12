from django.urls import path, include

from rest_framework.routers import DefaultRouter

from .views import (

    RegisterView,

    UserViewSet
)

from rest_framework_simplejwt.views import (

    TokenObtainPairView,

    TokenRefreshView,
)


# =========================================================
# ROUTER
# =========================================================

router = DefaultRouter()

router.register(
    r'users',
    UserViewSet,
    basename='users'
)


# =========================================================
# URLS
# =========================================================

urlpatterns = [

    # AUTH
    path(

        'register/',

        RegisterView.as_view(),

        name='register'
    ),

    path(

        'login/',

        TokenObtainPairView.as_view(),

        name='login'
    ),

    path(

        'token/refresh/',

        TokenRefreshView.as_view(),

        name='token_refresh'
    ),

    # USER APIs
    path('', include(router.urls)),
]