from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import RiderProfile
from .serializers import RiderProfileSerializer

class RiderProfileViewSet(viewsets.ModelViewSet):

    serializer_class = RiderProfileSerializer

    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        queryset = RiderProfile.objects.select_related(
            'user'
        ).all()

        stage = self.request.query_params.get('stage')

        status = self.request.query_params.get('status')

        if stage:
            queryset = queryset.filter(stage_name__icontains=stage)

        if status:
            queryset = queryset.filter(status=status)

        return queryset
    

from rest_framework import viewsets
from django.db.models import Q
from .models import RiderProfile
from .serializers import RiderProfileSerializer

class RiderProfileViewSet(viewsets.ModelViewSet):

    serializer_class = RiderProfileSerializer

    def get_queryset(self):

        queryset = RiderProfile.objects.select_related('user')

        search = self.request.query_params.get('search')

        stage = self.request.query_params.get('stage')

        status = self.request.query_params.get('status')

        if search:

            queryset = queryset.filter(

                Q(bike_plate_number__icontains=search) |
                Q(stage_name__icontains=search) |
                Q(village_name__icontains=search) |
                Q(user__email__icontains=search) |
                Q(user__phone_number__icontains=search)
            )

        if stage:
            queryset = queryset.filter(stage_name__icontains=stage)

        if status:
            queryset = queryset.filter(status=status)

        return queryset