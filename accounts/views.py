import secrets
from django.core.cache import cache
from rest_framework import (generics,viewsets,status)
from rest_framework.permissions import (AllowAny,IsAuthenticated)
from rest_framework.response import Response
from django.contrib.auth.hashers import make_password
from .models import User
from .serializers import (RegisterSerializer,UserSerializer,RiderSelfUpdateSerializer,DynamicUserSerializer,OTPVerificationSerializer,PasswordResetRequestSerializer,PasswordResetConfirmSerializer)
from .permissions import (IsManagementRole)
from .tasks import ( broadcast_user_event,refresh_users_cache,send_otp_task)


# =========================================================
# REGISTER VIEW (JWT ENABLED + CELERY)
# =========================================================

class RegisterView(generics.CreateAPIView):

    queryset = User.objects.all()

    serializer_class = RegisterSerializer

    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):

        response = super().create(request,*args,**kwargs)

        # =================================================
        # CELERY TASKS
        # =================================================

        broadcast_user_event.delay(

            f"New user registered: "
            f"{response.data.get('username')}"
        )

        refresh_users_cache.delay()

        return response


# =========================================================
# USER VIEWSET
# =========================================================

class UserViewSet(viewsets.ModelViewSet):

    queryset = User.objects.all().order_by('-created_at')

    permission_classes = [IsAuthenticated]

    filterset_fields = [

        'role',

        'is_verified',
    ]

    search_fields = [

        'username',

        'phone_number',

        'email',
    ]

    ordering_fields = [

        'created_at',
    ]

    ordering = ['-created_at']

    # =====================================================
    # QUERYSET SECURITY
    # =====================================================

    def get_queryset(self):

        user = self.request.user

        # MANAGEMENT USERS
        if user.role in [

            'super_admin',

            'stage_chairman',

            'stage_secretary',

            'stage_defense',
        ]:

            return User.objects.all()

        # NORMAL USERS
        return User.objects.filter(
            id=user.id
        )

    # =====================================================
    # SERIALIZER SELECTION
    # =====================================================

    def get_serializer_class(self):

        user = self.request.user

        # RIDER SELF UPDATE
        if user.role == 'rider':

            if self.action in [

                'update',

                'partial_update',
            ]:

                return RiderSelfUpdateSerializer

        # DEFAULT
        return DynamicUserSerializer

    # =====================================================
    # PERMISSIONS
    # =====================================================

    def get_permissions(self):

        user = self.request.user

        if not user.is_authenticated:

            return [AllowAny()]

        # MANAGEMENT USERS
        if user.role in [

            'super_admin',

            'stage_chairman',

            'stage_secretary',

            'stage_defense',
        ]:

            return [IsAuthenticated()]

        # RIDERS
        if user.role == 'rider':

            return [IsAuthenticated()]

        # GUEST RIDERS
        if user.role == 'guest_rider':

            if self.action in [

                'list',

                'retrieve',
            ]:

                return [IsAuthenticated()]

            return [IsManagementRole()]

        return [IsAuthenticated()]


# =========================================================
# OTP VERIFY VIEW
# =========================================================

class OTPVerifyView(generics.GenericAPIView):

    serializer_class = OTPVerificationSerializer

    permission_classes = [AllowAny]

    def post(self, request):

        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data['phone_number']

        otp = serializer.validated_data['otp_code']

        # =================================================
        # GET OTP FROM REDIS CACHE
        # =================================================

        cached_otp = cache.get(f"otp:{phone}")

        # =================================================
        # OTP DOES NOT EXIST / EXPIRED
        # =================================================

        if not cached_otp:

            return Response(
                {
                    "error": ( "OTP expired or invalid")
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # =================================================
        # INVALID OTP
        # =================================================

        if cached_otp != otp:

            return Response(
                {
                    "error": "Invalid OTP"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # =================================================
        # DELETE OTP AFTER SUCCESS
        # =================================================

        cache.delete(
            f"otp:{phone}"
        )

        return Response(
            {
                "message": (
                    "OTP verified successfully"
                ),
                "phone_number": phone
            },
            status=status.HTTP_200_OK
        )


# =========================================================
# PASSWORD RESET REQUEST VIEW
# =========================================================

class PasswordResetRequestView(generics.GenericAPIView):

    serializer_class = (PasswordResetRequestSerializer)

    permission_classes = [AllowAny]

    def post(self, request):

        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data['phone_number']

        # =================================================
        # CHECK USER EXISTS
        # =================================================

        if not User.objects.filter(phone_number=phone).exists():

            return Response(
                {
                    "error": (
                        "User with this phone "
                        "number does not exist"
                    )
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # =================================================
        # GENERATE SECURE OTP
        # =================================================

        otp_code = str(

            secrets.randbelow(900000)
            + 100000
        )

        # =================================================
        # SAVE OTP IN REDIS CACHE
        # EXPIRES IN 5 MINUTES
        # =================================================

        cache.set(

            f"otp:{phone}",

            otp_code,

            timeout=300
        )

        # =================================================
        # SEND OTP VIA CELERY TASK
        # =================================================

        send_otp_task.delay(

            phone,

            otp_code
        )

        return Response(
            {
                "message": (
                    "OTP sent successfully"
                ),
                "phone_number": phone
            },
            status=status.HTTP_200_OK
        )


# =========================================================
# PASSWORD RESET CONFIRM VIEW
# =========================================================

class PasswordResetConfirmView(generics.GenericAPIView):

    serializer_class = (PasswordResetConfirmSerializer)

    permission_classes = [AllowAny]

    def post(self, request):

        serializer = self.get_serializer(data=request.data)

        serializer.is_valid( raise_exception=True)

        phone = serializer.validated_data['phone_number']

        otp = serializer.validated_data['otp_code']

        new_password = serializer.validated_data['new_password']

        # =================================================
        # GET OTP FROM REDIS CACHE
        # =================================================

        cached_otp = cache.get(f"otp:{phone}")

        # =================================================
        # OTP INVALID / EXPIRED
        # =================================================

        if not cached_otp:

            return Response(
                {
                    "error": (
                        "OTP expired or invalid"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # =================================================
        # INVALID OTP
        # =================================================

        if cached_otp != otp:

            return Response(
                {
                    "error": "Invalid OTP"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # =================================================
        # GET USER
        # =================================================

        try:

            user = User.objects.get(phone_number=phone)

        except User.DoesNotExist:

            return Response(
                {
                    "error": "User not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # =================================================
        # UPDATE PASSWORD
        # =================================================

        user.password = make_password( new_password)

        user.save()

        # =================================================
        # DELETE OTP AFTER SUCCESS
        # =================================================

        cache.delete(f"otp:{phone}")

        return Response(
            {
                "message": (
                    "Password reset "
                    "successful"
                )
            },
            status=status.HTTP_200_OK
        )