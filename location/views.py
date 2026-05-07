from rest_framework import generics
from .models import RiderLocation
from .serializers import RiderLocationSerializer

class LocationCreateView(generics.CreateAPIView):
    queryset = RiderLocation.objects.all()
    serializer_class = RiderLocationSerializer


class LocationListView(generics.ListAPIView):
    queryset = RiderLocation.objects.all()
    serializer_class = RiderLocationSerializer