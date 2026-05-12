from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import RiderLocation
from .serializers import RiderLocationSerializer


class TrackingViewSet(viewsets.ModelViewSet):

    queryset = RiderLocation.objects.all()
    serializer_class = RiderLocationSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):

        serializer.save()

    # =====================================================
    # LIVE LOCATION UPDATE
    # =====================================================

    @action(detail=False, methods=['post'])
    def update_location(self, request):

        user = request.user

        data = request.data

        location = RiderLocation.objects.create(

            rider=getattr(user, 'rider_profile', None),

            guest_rider=getattr(user, 'guest_rider_profile', None),

            latitude=data['latitude'],

            longitude=data['longitude'],

            speed=data.get('speed', 0),
        )

        return Response({
            "status": "updated",
            "id": location.id
        })