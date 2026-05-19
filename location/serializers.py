from rest_framework import serializers

from .models import (
    RiderLocation,
    SuspiciousEvent
)


class RiderLocationSerializer(serializers.ModelSerializer):

    rider_name = serializers.CharField(
        source='rider.user.username',
        read_only=True
    )

    guest_rider_name = serializers.CharField(
        source='guest_rider.user.username',
        read_only=True
    )

    class Meta:

        model = RiderLocation

        fields = '__all__'


class SuspiciousEventSerializer(serializers.ModelSerializer):

    class Meta:

        model = SuspiciousEvent

        fields = '__all__'