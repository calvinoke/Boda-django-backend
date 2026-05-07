from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import EmergencyContact
from .serializers import EmergencyContactSerializer

class EmergencyContactViewSet(viewsets.ModelViewSet):

    serializer_class = EmergencyContactSerializer

    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        return EmergencyContact.objects.select_related(
            'rider'
        ).all()

    def perform_create(self, serializer):

        serializer.save(
            rider=self.request.user.rider_profile
        )