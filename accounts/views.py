import secrets
import hashlib
import logging
from datetime import timedelta

from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.contrib.auth import logout
from django.db import transaction
from django.utils import timezone
from django.db.models import Q

from rest_framework import generics, viewsets, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

# Import RefreshToken from SimpleJWT
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, SystemLog, LoginAttempt, PasswordResetToken
from .serializers import (
    RegisterSerializer,
    UserSerializer,
    RiderSelfUpdateSerializer,
    DynamicUserSerializer,
    OTPVerificationSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    OTPSendSerializer,
    AdminRoleUpdateSerializer,
    ChangePasswordSerializer,
)
from .tasks import broadcast_user_event, refresh_users_cache, send_otp_task
from .utils import (
    generate_otp,
    hash_otp,
    verify_otp,
    store_otp,
    verify_otp_code,
    rate_limited,
    reset_rate_limit,
    get_client_ip,
    get_user_agent,
)

# =========================================================
# LOGGING SETUP
# =========================================================

logger = logging.getLogger("users")
logger.setLevel(logging.INFO)

# =========================================================
# CUSTOM THROTTLE CLASSES
# =========================================================

class OTPRateThrottle(AnonRateThrottle):
    rate = '5/hour'

class LoginRateThrottle(AnonRateThrottle):
    rate = '10/hour'

class RegisterRateThrottle(AnonRateThrottle):
    rate = '3/hour'

# =========================================================
# REGISTER VIEW (FIXED)
# =========================================================

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    throttle_classes = [RegisterRateThrottle]

    @transaction.atomic()
    def create(self, request, *args, **kwargs):
        logger.info(f"Registration attempt from IP: {get_client_ip(request)}")
        
        response = super().create(request, *args, **kwargs)
        
        # Send verification OTP
        phone = response.data.get('phone_number')
        if phone:
            otp = generate_otp()
            store_otp(phone, otp, 'verification')
            
            # Send OTP via task
            send_otp_task.delay(phone, otp, 'verification')
            
            # Create system log
            user_id = response.data.get('id')
            if user_id:
                SystemLog.objects.create(
                    user_id=user_id,
                    action="USER_CREATED",
                    metadata={"phone": phone},
                    ip_address=get_client_ip(request),
                    user_agent=get_user_agent(request)
                )
        
        logger.info(f"User registered successfully: {response.data.get('username')}")
        
        broadcast_user_event.delay(f"New user registered: {response.data.get('username')}")
        refresh_users_cache.delay()
        
        return response

# =========================================================
# LOGIN VIEW (CUSTOM WITH LOCKOUT)
# =========================================================

class LoginView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    throttle_classes = [LoginRateThrottle]
    
    def post(self, request):
        from rest_framework_simplejwt.views import TokenObtainPairView
        from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
        
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response(
                {"error": "Username and password required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        ip_address = get_client_ip(request)
        
        # Check if user exists
        try:
            user = User.objects.get(Q(username=username) | Q(phone_number=username))
        except User.DoesNotExist:
            # Log failed attempt
            LoginAttempt.objects.create(
                phone_number=username if username.startswith('+256') else '',
                ip_address=ip_address,
                success=False
            )
            return Response(
                {"error": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Check if account is locked
        if user.is_locked():
            return Response(
                {"error": f"Account locked. Try again after {user.locked_until}"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check password
        if not user.check_password(password):
            user.failed_login_attempts += 1
            
            # Lock account after 5 failed attempts
            if user.failed_login_attempts >= 5:
                user.lock_account()
                SystemLog.objects.create(
                    user=user,
                    action="ACCOUNT_LOCKED",
                    metadata={"attempts": user.failed_login_attempts},
                    ip_address=ip_address,
                    user_agent=get_user_agent(request)
                )
            else:
                user.save(update_fields=['failed_login_attempts'])
            
            LoginAttempt.objects.create(
                phone_number=user.phone_number,
                ip_address=ip_address,
                success=False
            )
            
            return Response(
                {"error": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Login successful
        user.failed_login_attempts = 0
        user.last_login_ip = ip_address
        user.last_login_device = get_user_agent(request)
        user.save(update_fields=['failed_login_attempts', 'last_login_ip', 'last_login_device'])
        
        LoginAttempt.objects.create(
            phone_number=user.phone_number,
            ip_address=ip_address,
            success=True
        )
        
        SystemLog.objects.create(
            user=user,
            action="LOGIN",
            metadata={"ip": ip_address},
            ip_address=ip_address,
            user_agent=get_user_agent(request)
        )
        
        # Generate tokens using RefreshToken (now properly imported)
        refresh = RefreshToken.for_user(user)
        
        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": {
                "id": user.id,
                "username": user.username,
                "role": user.role,
                "is_verified": user.is_verified,
                "is_phone_verified": user.is_phone_verified,
                "is_email_verified": user.is_email_verified,
            }
        })

# =========================================================
# LOGOUT VIEW
# =========================================================

class LogoutView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if refresh_token:
                # RefreshToken is already imported at the top
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            # Log logout
            SystemLog.objects.create(
                user=request.user,
                action="LOGOUT",
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request)
            )
            
            return Response({"message": "Logged out successfully"}, status=200)
        except Exception as e:
            logger.error(f"Logout failed: {e}")
            return Response({"error": "Logout failed"}, status=400)

# =========================================================
# USER VIEWSET (FIXED)
# =========================================================

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("-created_at")
    permission_classes = [IsAuthenticated]

    filterset_fields = ["role", "is_verified", "is_active"]
    search_fields = ["username", "phone_number", "email"]
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        user = self.request.user
        
        # Super admin sees all
        if user.role == "super_admin":
            return User.objects.all()
        
        # Other privileged roles see all but with limited fields
        if user.role in ["stage_chairman", "stage_secretary", "stage_defense"]:
            return User.objects.all()
        
        # Riders see only themselves
        if user.role == "rider":
            return User.objects.filter(id=user.id)
        
        # Guest riders see only themselves
        return User.objects.filter(id=user.id)

    def get_serializer_class(self):
        user = self.request.user
        
        # Riders can update themselves
        if user.role == "rider" and self.action in ["update", "partial_update"]:
            return RiderSelfUpdateSerializer
        
        # Admins can update roles
        if user.role == "super_admin" and self.action in ["update", "partial_update"]:
            return AdminRoleUpdateSerializer
        
        return DynamicUserSerializer
    
    @transaction.atomic()
    def update(self, request, *args, **kwargs):
        # Log role changes
        instance = self.get_object()
        old_role = instance.role
        
        response = super().update(request, *args, **kwargs)
        
        if old_role != instance.role:
            SystemLog.objects.create(
                user=instance,
                action="ROLE_CHANGED",
                metadata={"old_role": old_role, "new_role": instance.role},
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request)
            )
        
        return response
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def change_password(self, request, pk=None):
        user = self.get_object()
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Check old password
        if not user.check_password(serializer.validated_data['old_password']):
            return Response(
                {"error": "Old password is incorrect"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Set new password
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        SystemLog.objects.create(
            user=user,
            action="PASSWORD_CHANGED",
            metadata={"changed_by": request.user.username},
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request)
        )
        
        return Response({"message": "Password changed successfully"}, status=200)

# =========================================================
# OTP SEND VIEW (FIXED)
# =========================================================

class OTPSendView(generics.GenericAPIView):
    serializer_class = OTPSendSerializer
    permission_classes = [AllowAny]
    throttle_classes = [OTPRateThrottle]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone_number"]
        purpose = serializer.validated_data.get("purpose", "verification")
        ip_address = get_client_ip(request)

        logger.info(f"OTP send request: {phone} for purpose: {purpose}")

        # Check rate limiting by IP and phone
        ip_key = f"ip:{ip_address}"
        if rate_limited(ip_key):
            return Response(
                {"error": "Too many OTP requests from this IP"},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        if rate_limited(phone):
            return Response(
                {"error": "Too many OTP requests for this number"},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        # Check if user exists based on purpose
        if purpose in ["password_reset", "verification"]:
            user_exists = User.objects.filter(phone_number=phone).exists()
            if purpose == "password_reset" and not user_exists:
                return Response(
                    {"error": "User not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            if purpose == "verification" and not user_exists:
                # Allow OTP for new users during registration
                pass

        otp = generate_otp()
        store_otp(phone, otp, purpose)

        # Send OTP via Celery
        send_otp_task.delay(phone, otp, purpose)

        logger.info(f"OTP sent successfully: {phone}")

        return Response(
            {"message": "OTP sent successfully", "purpose": purpose},
            status=200,
        )

# =========================================================
# OTP VERIFY VIEW (FIXED)
# =========================================================

class OTPVerifyView(generics.GenericAPIView):
    serializer_class = OTPVerificationSerializer
    permission_classes = [AllowAny]
    throttle_classes = [OTPRateThrottle]

    @transaction.atomic()
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone_number"]
        otp = serializer.validated_data["otp_code"]
        purpose = serializer.validated_data.get("purpose", "verification")
        ip_address = get_client_ip(request)

        logger.info(f"OTP verification attempt: {phone} for purpose: {purpose}")

        if rate_limited(phone):
            return Response(
                {"error": "Too many attempts. Try again later."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        if not verify_otp_code(phone, otp, purpose):
            return Response(
                {"error": "Invalid or expired OTP"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update user verification status
        try:
            user = User.objects.get(phone_number=phone)
            
            if purpose == "verification":
                user.is_phone_verified = True
                user.is_verified = True
                user.save(update_fields=['is_phone_verified', 'is_verified'])
            elif purpose == "phone_change":
                # Phone change verification is handled in serializer
                pass
            
            SystemLog.objects.create(
                user=user,
                action="OTP_VERIFIED",
                metadata={"phone": phone, "purpose": purpose},
                ip_address=ip_address,
                user_agent=get_user_agent(request)
            )
        except User.DoesNotExist:
            pass

        reset_rate_limit(phone)

        return Response(
            {"message": "OTP verified successfully", "phone_number": phone},
            status=200,
        )

# =========================================================
# PASSWORD RESET REQUEST VIEW (FIXED)
# =========================================================

class PasswordResetRequestView(generics.GenericAPIView):
    serializer_class = PasswordResetRequestSerializer
    permission_classes = [AllowAny]
    throttle_classes = [OTPRateThrottle]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone_number"]
        ip_address = get_client_ip(request)

        if rate_limited(phone):
            return Response(
                {"error": "Too many attempts"},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        if not User.objects.filter(phone_number=phone).exists():
            return Response(
                {"error": "User does not exist"},
                status=status.HTTP_404_NOT_FOUND
            )

        otp = generate_otp()
        store_otp(phone, otp, 'password_reset')

        send_otp_task.delay(phone, otp, 'password_reset')

        SystemLog.objects.create(
            action="PASSWORD_RESET_REQUEST",
            metadata={"phone": phone},
            ip_address=ip_address,
            user_agent=get_user_agent(request)
        )

        return Response(
            {"message": "OTP sent successfully"},
            status=200
        )

# =========================================================
# PASSWORD RESET CONFIRM VIEW (FIXED)
# =========================================================

class PasswordResetConfirmView(generics.GenericAPIView):
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [AllowAny]
    throttle_classes = [OTPRateThrottle]

    @transaction.atomic()
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone_number"]
        otp = serializer.validated_data["otp_code"]
        new_password = serializer.validated_data["new_password"]
        ip_address = get_client_ip(request)

        if rate_limited(phone):
            return Response(
                {"error": "Too many attempts"},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        if not verify_otp_code(phone, otp, 'password_reset'):
            return Response(
                {"error": "Invalid or expired OTP"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(phone_number=phone)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        user.set_password(new_password)
        user.save()

        reset_rate_limit(phone)

        SystemLog.objects.create(
            user=user,
            action="PASSWORD_RESET",
            metadata={"phone": phone},
            ip_address=ip_address,
            user_agent=get_user_agent(request)
        )

        return Response(
            {"message": "Password reset successful"},
            status=200
        )

# =========================================================
# VERIFY PHONE VIEW
# =========================================================

class VerifyPhoneView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        
        if user.is_phone_verified:
            return Response(
                {"message": "Phone already verified"},
                status=200
            )
        
        # Send verification OTP
        otp = generate_otp()
        store_otp(user.phone_number, otp, 'verification')
        send_otp_task.delay(user.phone_number, otp, 'verification')
        
        return Response(
            {"message": "Verification OTP sent"},
            status=200
        )