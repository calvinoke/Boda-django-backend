from rest_framework import serializers
from .models import RiderVerification

class RiderVerificationSerializer(serializers.ModelSerializer):

    class Meta:

        model = RiderVerification

        fields = '__all__'

        read_only_fields = [
            'is_verified',
            'verified_by',
            'verified_at',
        ]