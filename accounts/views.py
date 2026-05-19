
from rest_framework import (
    generics,
    viewsets
)
from rest_framework.permissions import (

    AllowAny,

    IsAuthenticated
)
from .models import User
from .serializers import (

    RegisterSerializer,

    UserSerializer,

    RiderSelfUpdateSerializer
)

from .permissions import (
    IsManagementRole,
)

from .tasks import (

    broadcast_user_event,

    refresh_users_cache
)


# =========================================================
# REGISTER VIEW
# =========================================================

class RegisterView(

    generics.CreateAPIView
):

    queryset = User.objects.all()

    serializer_class = RegisterSerializer

    permission_classes = [AllowAny]

    def perform_create(self, serializer):

        user = serializer.save()

        # =================================================
        # CELERY + REDIS + WEBSOCKETS
        # =================================================

        broadcast_user_event.delay(

            f"New user registered: {user.username}"
        )

        refresh_users_cache.delay()


# =========================================================
# USER VIEWSET
# =========================================================

class UserViewSet(viewsets.ModelViewSet):

    queryset = User.objects.all().order_by(
        '-created_at'
    )

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
    # SERIALIZER CONTROL
    # =====================================================

    def get_serializer_class(self):

        user = self.request.user

        if user.role == 'rider':

            if self.action in [

                'update',

                'partial_update',
            ]:
                return RiderSelfUpdateSerializer

        return UserSerializer

    # =====================================================
    # PERMISSIONS
    # =====================================================

    def get_permissions(self):

        if self.request.user.role in [

            'super_admin',

            'stage_chairman',

            'stage_secretary',

            'stage_defense',
        ]:
            return [IsAuthenticated()]

        if self.request.user.role == 'rider':

            return [IsAuthenticated()]

        if self.request.user.role == 'guest_rider':

            if self.action in [

                'list',

                'retrieve',
            ]:
                return [IsAuthenticated()]

            return [IsManagementRole()]

        return [IsAuthenticated()]