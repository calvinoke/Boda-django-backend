from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ( RegisterView,UserViewSet,OTPVerifyView,PasswordResetRequestView,PasswordResetConfirmView)
from rest_framework_simplejwt.views import (TokenObtainPairView,TokenRefreshView,)


# =========================================================
# ROUTER
# =========================================================

router = DefaultRouter()

router.register( r'users', UserViewSet, basename='users')


# =========================================================
# URLS
# =========================================================

urlpatterns = [

    # =====================================================
    # AUTH - JWT
    # =====================================================

    path('register/', RegisterView.as_view(),name='register'),

    path('login/', TokenObtainPairView.as_view(), name='login'),

    path( 'token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # =====================================================
    # OTP AUTH SYSTEM
    # =====================================================

    path('otp/verify/',OTPVerifyView.as_view(), name='otp_verify'),

    # =====================================================
    # PASSWORD RESET FLOW
    # =====================================================

    path('password-reset/',PasswordResetRequestView.as_view(), name='password_reset'),

    path( 'password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),

    # =====================================================
    # USER APIs
    # =====================================================

    path('',include(router.urls)),
]