from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import RiderVerification
from .serializers import RiderVerificationSerializer

class RiderVerificationViewSet(viewsets.ModelViewSet):

    serializer_class = RiderVerificationSerializer

    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        return RiderVerification.objects.select_related(
            'rider',
            'verified_by'
        ).all()

    def perform_create(self, serializer):

        serializer.save(
            rider=self.request.user.rider_profile
        )