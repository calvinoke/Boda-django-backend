from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import (
    RiderProfile,
    RiderDetails,
    GuestRider
)

from .serializers import (

    RiderProfileSerializer,
    RiderSelfUpdateSerializer,

    RiderDetailsSerializer,

    GuestRiderSerializer
)

from accounts.permissions import (

    IsManagementRole,

    IsManagementOrOwner,

    IsRiderSelfUpdate,
)
    

# =========================================================
# RIDER PROFILE VIEWSET
# =========================================================

class RiderProfileViewSet(viewsets.ModelViewSet):

    queryset = RiderProfile.objects.select_related(
        'user',
        'stage'
    ).prefetch_related(
        'details'
    )

    filterset_fields = [

        'status',
        'is_verified',
        'is_blacklisted',
        'stage',
    ]

    search_fields = [

        'bike_plate_number',

        'national_id_number',

        'rider_phone_number',

        'user__username',

        'user__first_name',

        'user__last_name',
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

        queryset = self.queryset

        # MANAGEMENT
        if user.role in [

            'super_admin',

            'stage_chairman',

            'stage_secretary',

            'stage_defense'
        ]:
            return queryset

        # RIDER ONLY OWN PROFILE
        return queryset.filter(user=user)

    # =====================================================
    # SERIALIZER CONTROL
    # =====================================================

    def get_serializer_class(self):

        if (

            self.request.user.role == 'rider' and

            self.action in ['update', 'partial_update']
        ):
            return RiderSelfUpdateSerializer

        return RiderProfileSerializer

    # =====================================================
    # PERMISSIONS
    # =====================================================

    def get_permissions(self):

        # MANAGEMENT FULL CRUD
        if self.request.user.role in [

            'super_admin',

            'stage_chairman',

            'stage_secretary',

            'stage_defense'
        ]:
            return [IsAuthenticated()]

        # RIDER SELF ACCESS
        if self.request.user.role == 'rider':
            return [IsRiderSelfUpdate()]

        # GUEST RIDER READ ONLY
        return [IsAuthenticated()]


# =========================================================
# RIDER DETAILS VIEWSET
# =========================================================

class RiderDetailsViewSet(viewsets.ModelViewSet):

    serializer_class = RiderDetailsSerializer

    queryset = RiderDetails.objects.select_related(
        'rider',
        'rider__user'
    )

    # =====================================================
    # QUERYSET SECURITY
    # =====================================================

    def get_queryset(self):

        user = self.request.user

        if user.role in [

            'super_admin',

            'stage_chairman',

            'stage_secretary',

            'stage_defense'
        ]:
            return self.queryset

        return self.queryset.filter(
            rider__user=user
        )

    # =====================================================
    # PERMISSIONS
    # =====================================================

    def get_permissions(self):

        return [IsAuthenticated()]

    # =====================================================
    # AUTO LINK RIDER
    # =====================================================

    def perform_create(self, serializer):

        rider_profile = RiderProfile.objects.get(
            user=self.request.user
        )

        serializer.save(
            rider=rider_profile
        )


# =========================================================
# GUEST RIDER VIEWSET
# =========================================================

class GuestRiderViewSet(viewsets.ModelViewSet):

    queryset = GuestRider.objects.select_related(
        'user'
    )

    serializer_class = GuestRiderSerializer

    filterset_fields = [

        'status',

        'is_blacklisted',

        'current_area',
    ]

    search_fields = [

        'bike_plate_number',

        'national_id_number',

        'phone_number',

        'user__username',
    ]

    ordering = ['-created_at']

    # =====================================================
    # QUERYSET SECURITY
    # =====================================================

    def get_queryset(self):

        user = self.request.user

        # MANAGEMENT
        if user.role in [

            'super_admin',

            'stage_chairman',

            'stage_secretary',

            'stage_defense'
        ]:
            return self.queryset

        # GUEST RIDER ONLY OWN RECORD
        return self.queryset.filter(
            user=user
        )

    # =====================================================
    # PERMISSIONS
    # =====================================================

    def get_permissions(self):

        return [IsAuthenticated()]