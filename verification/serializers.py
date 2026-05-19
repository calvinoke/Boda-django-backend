from rest_framework import serializers
from .models import (

    RiderVerification,

    VerificationRequest
)


# =========================================================
# RIDER VERIFICATION SERIALIZER
# =========================================================

class RiderVerificationSerializer(serializers.ModelSerializer):

    rider_username = serializers.CharField(
        source='rider.user.username',
        read_only=True
    )

    verified_by_username = serializers.CharField(
        source='verified_by.username',
        read_only=True
    )

    class Meta:

        model = RiderVerification

        fields = '__all__'

        read_only_fields = (

            'is_verified',

            'verified_by',

            'verified_at',
        )


# =========================================================
# VERIFICATION REQUEST SERIALIZER
# =========================================================

class VerificationRequestSerializer(serializers.ModelSerializer):

    username = serializers.CharField(
        source='user.username',
        read_only=True
    )

    class Meta:

        model = VerificationRequest

        fields = '__all__'