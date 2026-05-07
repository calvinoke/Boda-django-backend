from rest_framework import serializers
from .models import RiderLocation

class RiderLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiderLocation
        fields = '__all__'