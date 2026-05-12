from rest_framework import viewsets
from .models import Fine, FineType
from .serializers import FineSerializer, FineTypeSerializer
from .permissions import CanIssueFine, CanViewFines


# =========================================================
# FINE TYPE VIEWSET (ADMIN CONFIG)
# =========================================================

class FineTypeViewSet(viewsets.ModelViewSet):

    queryset = FineType.objects.all()
    serializer_class = FineTypeSerializer
    permission_classes = [CanIssueFine]


# =========================================================
# FINE VIEWSET
# =========================================================

class FineViewSet(viewsets.ModelViewSet):

    queryset = Fine.objects.select_related(
        'issued_by',
        'rider',
        'guest_rider',
        'stage',
        'fine_type'
    )

    serializer_class = FineSerializer
    permission_classes = [CanViewFines]

    def perform_create(self, serializer):

        serializer.save(issued_by=self.request.user)

    def get_queryset(self):

        user = self.request.user

        # MANAGEMENT SEE ALL
        if user.role in [
            'super_admin',
            'stage_chairman',
            'stage_secretary',
            'stage_defense'
        ]:
            return Fine.objects.all()

        # RIDERS SEE OWN FINES
        if user.role == 'rider':
            return Fine.objects.filter(rider__user=user)

        # GUEST RIDERS SEE OWN FINES
        if user.role == 'guest_rider':
            return Fine.objects.filter(guest_rider__user=user)

        return Fine.objects.none()