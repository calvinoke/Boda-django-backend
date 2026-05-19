from rest_framework import serializers
from .models import RiderProfile, RiderDetails, GuestRider


class RiderDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiderDetails
        fields = '__all__'
        read_only_fields = ['rider', 'created_at', 'updated_at']


class RiderProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = RiderProfile
        fields = '__all__'
        read_only_fields = [
            'status',
            'is_verified',
            'is_blacklisted',
            'suspicious_activity_score',
            'created_at',
            'updated_at',
        ]


class GuestRiderSerializer(serializers.ModelSerializer):

    class Meta:
        model = GuestRider
        fields = '__all__'
        read_only_fields = [
            'is_blacklisted',
            'suspicious_activity_score',
            'created_at',
            'updated_at',
        ]