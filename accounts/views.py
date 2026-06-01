import secrets
import hashlib
import logging
from django.core.cache import cache
from django.contrib.auth import get_user_model
from rest_framework import generics, viewsets, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth.hashers import make_password
from .models import User, SystemLog
from .serializers import (
    RegisterSerializer,
    UserSerializer,
    RiderSelfUpdateSerializer,
    DynamicUserSerializer,
    OTPVerificationSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer
)

from .permissions import IsManagementRole
from .tasks import broadcast_user_event, refresh_users_cache, send_otp_task


# =========================================================
# LOGGING SETUP
# =========================================================

logger = logging.getLogger("users")
logger.setLevel(logging.INFO)


# =========================================================
# OTP SECURITY HELPERS
# =========================================================

def hash_otp(otp: str) -> str:
    return hashlib.sha256(otp.encode()).hexdigest()


def verify_otp(otp: str, hashed: str) -> bool:
    return hash_otp(otp) == hashed


# =========================================================
# RATE LIMITING (OTP ABUSE PROTECTION)
# =========================================================

def rate_limited(phone: str, limit: int = 5, window: int = 300) -> bool:
    key = f"otp_attempts:{phone}"
    attempts = cache.get(key, 0)

    if attempts >= limit:
        return True

    cache.set(key, attempts + 1, timeout=window)
    return False


def reset_rate_limit(phone: str):
    cache.delete(f"otp_attempts:{phone}")


# =========================================================
# REGISTER VIEW
# =========================================================

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        logger.info(f"Registration attempt: {request.data.get('username')}")

        response = super().create(request, *args, **kwargs)

        username = response.data.get("username")

        logger.info(f"User registered successfully: {username}")

        broadcast_user_event.delay(f"New user registered: {username}")
        refresh_users_cache.delay()

        return response


# =========================================================
# USER VIEWSET
# =========================================================

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("-created_at")
    permission_classes = [IsAuthenticated]

    filterset_fields = ["role", "is_verified"]
    search_fields = ["username", "phone_number", "email"]
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        user = self.request.user

        if user.role in [
            "super_admin",
            "stage_chairman",
            "stage_secretary",
            "stage_defense",
        ]:
            return User.objects.all()

        return User.objects.filter(id=user.id)

    def get_serializer_class(self):
        user = self.request.user

        if user.role == "rider" and self.action in ["update", "partial_update"]:
            return RiderSelfUpdateSerializer

        return DynamicUserSerializer


# =========================================================
# OTP VERIFY VIEW (SECURE)
# =========================================================

class OTPVerifyView(generics.GenericAPIView):
    serializer_class = OTPVerificationSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone_number"]
        otp = serializer.validated_data["otp_code"]

        logger.info(f"OTP verification attempt: {phone}")

        if rate_limited(phone):
            logger.warning(f"OTP rate limit exceeded: {phone}")
            return Response(
                {"error": "Too many attempts. Try again later."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        cached_otp = cache.get(f"otp:{phone}")

        if not cached_otp:
            logger.warning(f"OTP expired: {phone}")
            return Response({"error": "OTP expired or invalid"}, status=400)

        if not verify_otp(otp, cached_otp):
            logger.warning(f"Invalid OTP: {phone}")
            return Response({"error": "Invalid OTP"}, status=400)

        cache.delete(f"otp:{phone}")
        reset_rate_limit(phone)

        SystemLog.objects.create(
            action="OTP_VERIFIED",
            metadata={"phone": phone},
        )

        logger.info(f"OTP verified successfully: {phone}")

        return Response(
            {"message": "OTP verified successfully", "phone_number": phone},
            status=200,
        )


# =========================================================
# PASSWORD RESET REQUEST VIEW
# =========================================================

class PasswordResetRequestView(generics.GenericAPIView):
    serializer_class = PasswordResetRequestSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone_number"]

        logger.info(f"Password reset request: {phone}")

        if rate_limited(phone):
            logger.warning(f"Password reset rate limit hit: {phone}")
            return Response({"error": "Too many attempts"}, status=429)

        if not User.objects.filter(phone_number=phone).exists():
            logger.warning(f"Password reset for unknown user: {phone}")
            return Response({"error": "User does not exist"}, status=404)

        otp_code = str(secrets.randbelow(900000) + 100000)

        cache.set(
            f"otp:{phone}",
            hash_otp(otp_code),
            timeout=300,
        )

        send_otp_task.delay(phone, otp_code)

        logger.info(f"OTP sent for password reset: {phone}")

        return Response({"message": "OTP sent successfully"}, status=200)


# =========================================================
# PASSWORD RESET CONFIRM VIEW
# =========================================================

class PasswordResetConfirmView(generics.GenericAPIView):
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone_number"]
        otp = serializer.validated_data["otp_code"]
        new_password = serializer.validated_data["new_password"]

        logger.info(f"Password reset attempt: {phone}")

        cached_otp = cache.get(f"otp:{phone}")

        if not cached_otp or not verify_otp(otp, cached_otp):
            logger.warning(f"Password reset failed OTP: {phone}")
            return Response({"error": "Invalid OTP"}, status=400)

        try:
            user = User.objects.get(phone_number=phone)
        except User.DoesNotExist:
            logger.error(f"Password reset user not found: {phone}")
            return Response({"error": "User not found"}, status=404)

        user.set_password(new_password)
        user.save()

        cache.delete(f"otp:{phone}")
        reset_rate_limit(phone)

        SystemLog.objects.create(
            action="PASSWORD_RESET",
            metadata={"phone": phone},
        )

        logger.info(f"Password reset successful: {phone}")

        return Response({"message": "Password reset successful"}, status=200)