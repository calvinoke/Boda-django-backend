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
    PRIVILEGED_ROLES,
)
from .tasks import (
    broadcast_user_event, 
    refresh_users_cache, 
    send_otp_task,
    send_welcome_email_task,
)
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
# REGISTER VIEW
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
        
        phone = response.data.get('phone_number')
        if phone:
            otp = generate_otp()
            store_otp(phone, otp, 'verification')
            send_otp_task.delay(phone, otp, 'verification')
            
            user_id = response.data.get('id')
            if user_id:
                SystemLog.objects.create(
                    user_id=user_id,
                    action="USER_CREATED",
                    metadata={"phone": phone},
                    ip_address=get_client_ip(request),
                    user_agent=get_user_agent(request)
                )
                
                # Send welcome email asynchronously
                send_welcome_email_task.delay(user_id)
        
        logger.info(f"User registered successfully: {response.data.get('username')}")
        
        broadcast_user_event.delay(f"New user registered: {response.data.get('username')}")
        refresh_users_cache.delay()
        
        return response

# =========================================================
# LOGIN VIEW - UPDATED WITH EMAIL SUPPORT
# =========================================================

class LoginView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    throttle_classes = [LoginRateThrottle]
    
    def post(self, request):
        username_or_email = request.data.get('username')
        password = request.data.get('password')
        
        if not username_or_email or not password:
            return Response(
                {"error": "Username/Email and password required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        ip_address = get_client_ip(request)
        
        try:
            # Allow login with username, email, or phone number
            user = User.objects.get(
                Q(username=username_or_email) | 
                Q(email=username_or_email) | 
                Q(phone_number=username_or_email)
            )
        except User.DoesNotExist:
            LoginAttempt.objects.create(
                phone_number=username_or_email if username_or_email.startswith('+256') else '',
                ip_address=ip_address,
                success=False
            )
            return Response(
                {"error": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if user.is_locked():
            return Response(
                {"error": f"Account locked. Try again after {user.locked_until}"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if not user.check_password(password):
            user.failed_login_attempts += 1
            
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
        
        refresh = RefreshToken.for_user(user)
        
        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
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
                token = RefreshToken(refresh_token)
                token.blacklist()
            
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
# USER VIEWSET (UPDATED WITH ROLE MANAGEMENT & EMAIL FEATURES)
# =========================================================

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("-created_at")
    permission_classes = [IsAuthenticated]

    filterset_fields = ["role", "is_verified", "is_active", "is_email_verified"]
    search_fields = ["username", "phone_number", "email"]
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        user = self.request.user
        
        if user.role == "super_admin":
            return User.objects.all()
        
        if user.role in ["stage_chairman", "stage_secretary", "stage_defense"]:
            return User.objects.all()
        
        if user.role == "rider":
            return User.objects.filter(id=user.id)
        
        return User.objects.filter(id=user.id)

    def get_serializer_class(self):
        user = self.request.user
        
        if user.role == "rider" and self.action in ["update", "partial_update"]:
            return RiderSelfUpdateSerializer
        
        if user.role == "super_admin" and self.action in ["update", "partial_update"]:
            return AdminRoleUpdateSerializer
        
        return DynamicUserSerializer
    
    @transaction.atomic()
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        old_role = instance.role
        old_email = instance.email
        
        response = super().update(request, *args, **kwargs)
        
        # Log role changes
        if old_role != instance.role:
            SystemLog.objects.create(
                user=instance,
                action="ROLE_CHANGED",
                metadata={
                    "old_role": old_role, 
                    "new_role": instance.role,
                    "changed_by": request.user.username
                },
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request)
            )
        
        # Log email changes
        if old_email != instance.email and instance.email:
            SystemLog.objects.create(
                user=instance,
                action="EMAIL_CHANGED",
                metadata={
                    "old_email": old_email,
                    "new_email": instance.email,
                    "changed_by": request.user.username
                },
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request)
            )
            
            # Reset email verification status
            instance.is_email_verified = False
            instance.save(update_fields=['is_email_verified'])
        
        return response
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    @transaction.atomic()
    def change_role(self, request, pk=None):
        """Change user role (Super Admin only)"""
        user = self.get_object()
        
        if request.user.role != "super_admin":
            return Response(
                {"error": "Only super admins can change roles"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        new_role = request.data.get('role')
        if not new_role:
            return Response(
                {"error": "Role is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if new_role not in dict(User.ROLE_CHOICES).keys():
            return Response(
                {"error": "Invalid role"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        old_role = user.role
        user.role = new_role
        
        # Auto-verify if promoting to admin
        if new_role in PRIVILEGED_ROLES:
            user.is_verified = True
            user.is_phone_verified = True
            user.is_email_verified = True
        
        user.save(update_fields=['role', 'is_verified', 'is_phone_verified', 'is_email_verified'])
        
        SystemLog.objects.create(
            user=user,
            action="ROLE_CHANGED",
            metadata={
                "old_role": old_role, 
                "new_role": new_role,
                "changed_by": request.user.username
            },
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request)
        )
        
        return Response({
            "message": f"User {user.username} role changed from {old_role} to {new_role}",
            "user": {
                "id": user.id,
                "username": user.username,
                "role": user.role,
                "is_verified": user.is_verified
            }
        })
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    @transaction.atomic()
    def promote(self, request, pk=None):
        """Promote user to admin role"""
        user = self.get_object()
        
        if request.user.role != "super_admin":
            return Response(
                {"error": "Only super admins can promote users"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        new_role = request.data.get('role', 'stage_chairman')
        
        if new_role not in PRIVILEGED_ROLES:
            return Response(
                {"error": f"Invalid admin role. Choose from: {', '.join(PRIVILEGED_ROLES)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        old_role = user.role
        user.role = new_role
        user.is_verified = True
        user.is_phone_verified = True
        user.is_email_verified = True
        user.save(update_fields=['role', 'is_verified', 'is_phone_verified', 'is_email_verified'])
        
        SystemLog.objects.create(
            user=user,
            action="ROLE_CHANGED",
            metadata={
                "old_role": old_role,
                "new_role": new_role,
                "promoted_by": request.user.username
            },
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request)
        )
        
        return Response({
            "message": f"User {user.username} promoted from {old_role} to {new_role}",
            "user": {
                "id": user.id,
                "username": user.username,
                "role": user.role,
                "is_verified": user.is_verified
            }
        })
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    @transaction.atomic()
    def demote(self, request, pk=None):
        """Demote user from admin to rider"""
        user = self.get_object()
        
        if request.user.role != "super_admin":
            return Response(
                {"error": "Only super admins can demote users"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if user.role == "super_admin":
            return Response(
                {"error": "Cannot demote super_admin"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        old_role = user.role
        user.role = "rider"
        user.save(update_fields=['role'])
        
        SystemLog.objects.create(
            user=user,
            action="ROLE_CHANGED",
            metadata={
                "old_role": old_role,
                "new_role": "rider",
                "demoted_by": request.user.username
            },
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request)
        )
        
        return Response({
            "message": f"User {user.username} demoted from {old_role} to rider",
            "user": {
                "id": user.id,
                "username": user.username,
                "role": user.role
            }
        })
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def change_password(self, request, pk=None):
        user = self.get_object()
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        if not user.check_password(serializer.validated_data['old_password']):
            return Response(
                {"error": "Old password is incorrect"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
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
    # EMAIL SEARCH - Admin Only
    # =========================================================
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def search_by_email(self, request):
        """Search users by email (Admin only)"""
        if request.user.role not in ["super_admin", "stage_chairman", "stage_secretary", "stage_defense"]:
            return Response(
                {"error": "Permission denied. Admin access required."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        email = request.query_params.get('email')
        if not email:
            return Response(
                {"error": "Email parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(email__iexact=email)
            serializer = UserSerializer(user)
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found with this email"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    # =========================================================
    # EMAIL UPDATE - Admin Only
    # =========================================================
    
    @action(detail=False, methods=['patch'], permission_classes=[IsAuthenticated])
    def update_by_email(self, request):
        """Update user by email (Admin only)"""
        if request.user.role != "super_admin":
            return Response(
                {"error": "Only super admins can update users by email"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        email = request.data.get('email')
        if not email:
            return Response(
                {"error": "Email is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(email__iexact=email)
            serializer = AdminRoleUpdateSerializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                old_role = user.role
                serializer.save()
                
                # Log the update
                SystemLog.objects.create(
                    user=user,
                    action="OTHER",
                    metadata={
                        "updated_by": request.user.username,
                        "updated_fields": list(request.data.keys())
                    },
                    ip_address=get_client_ip(request),
                    user_agent=get_user_agent(request)
                )
                
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found with this email"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    # =========================================================
    # EMAIL VERIFICATION ENDPOINTS
    # =========================================================
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def verify_email(self, request):
        """Request email verification (send OTP to email)"""
        user = request.user
        
        if user.is_email_verified:
            return Response(
                {"message": "Email already verified"},
                status=status.HTTP_200_OK
            )
        
        if not user.email:
            return Response(
                {"error": "No email address associated with this account"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate OTP for email verification
        otp = generate_otp()
        store_otp(user.email, otp, 'email_verification')
        
        # Send OTP via email
        from .tasks import send_otp_email_task
        send_otp_email_task.delay(user.id, otp, 'email_verification')
        
        SystemLog.objects.create(
            user=user,
            action="OTP_SENT",
            metadata={"purpose": "email_verification"},
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request)
        )
        
        return Response(
            {"message": "Verification OTP sent to your email"},
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def confirm_email_verification(self, request):
        """Confirm email verification with OTP"""
        user = request.user
        otp_code = request.data.get('otp_code')
        
        if not otp_code:
            return Response(
                {"error": "OTP code is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if user.is_email_verified:
            return Response(
                {"message": "Email already verified"},
                status=status.HTTP_200_OK
            )
        
        if not user.email:
            return Response(
                {"error": "No email address associated with this account"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify OTP
        if not verify_otp_code(user.email, otp_code, 'email_verification'):
            return Response(
                {"error": "Invalid or expired OTP"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Mark email as verified
        user.is_email_verified = True
        user.save(update_fields=['is_email_verified'])
        
        SystemLog.objects.create(
            user=user,
            action="EMAIL_VERIFIED",
            metadata={"email": user.email},
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request)
        )
        
        return Response(
            {"message": "Email verified successfully"},
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def resend_email_verification(self, request, pk=None):
        """Resend email verification OTP (Admin or Self)"""
        user = self.get_object()
        
        # Check permission (self or admin)
        if request.user.id != user.id and request.user.role != "super_admin":
            return Response(
                {"error": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if user.is_email_verified:
            return Response(
                {"message": "Email already verified"},
                status=status.HTTP_200_OK
            )
        
        if not user.email:
            return Response(
                {"error": "No email address associated with this account"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate and send OTP
        otp = generate_otp()
        store_otp(user.email, otp, 'email_verification')
        
        from .tasks import send_otp_email_task
        send_otp_email_task.delay(user.id, otp, 'email_verification')
        
        SystemLog.objects.create(
            user=user,
            action="OTP_SENT",
            metadata={"purpose": "email_verification_resend"},
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request)
        )
        
        return Response(
            {"message": "Verification OTP resent to your email"},
            status=status.HTTP_200_OK
        )

# =========================================================
# OTP SEND VIEW
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

        if purpose in ["password_reset", "verification"]:
            user_exists = User.objects.filter(phone_number=phone).exists()
            if purpose == "password_reset" and not user_exists:
                return Response(
                    {"error": "User not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

        otp = generate_otp()
        store_otp(phone, otp, purpose)
        send_otp_task.delay(phone, otp, purpose)

        logger.info(f"OTP sent successfully: {phone}")

        return Response(
            {"message": "OTP sent successfully", "purpose": purpose},
            status=200,
        )

# =========================================================
# OTP VERIFY VIEW
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

        try:
            user = User.objects.get(phone_number=phone)
            
            if purpose == "verification":
                user.is_phone_verified = True
                user.is_verified = True
                user.save(update_fields=['is_phone_verified', 'is_verified'])
            
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
# PASSWORD RESET REQUEST VIEW
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
# PASSWORD RESET CONFIRM VIEW
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
        
        otp = generate_otp()
        store_otp(user.phone_number, otp, 'verification')
        send_otp_task.delay(user.phone_number, otp, 'verification')
        
        return Response(
            {"message": "Verification OTP sent"},
            status=200
        )