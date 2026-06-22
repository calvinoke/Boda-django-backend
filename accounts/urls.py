from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RegisterView,
    LoginView,
    LogoutView,
    UserViewSet,
    OTPVerifyView,
    OTPSendView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    VerifyPhoneView,
)
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='users')

urlpatterns = [

    # ======================
    # AUTH - JWT
    # ======================
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),

    # ======================
    # OTP SYSTEM
    # ======================
    path('otp/send/', OTPSendView.as_view(), name='otp_send'),
    path('otp/verify/', OTPVerifyView.as_view(), name='otp_verify'),
    path('verify-phone/', VerifyPhoneView.as_view(), name='verify_phone'),

    # ======================
    # PASSWORD RESET
    # ======================
    path('password-reset/', PasswordResetRequestView.as_view(), name='password_reset'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),

    # ======================
    # USERS
    # ======================
    path('', include(router.urls)),
]