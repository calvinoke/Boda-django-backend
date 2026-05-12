from rest_framework import serializers

from .models import (
    RiderProfile,
    RiderDetails,
    GuestRider
)


# =========================================================
# RIDER DETAILS SERIALIZER
# =========================================================

class RiderDetailsSerializer(serializers.ModelSerializer):

    class Meta:

        model = RiderDetails

        fields = '__all__'

        read_only_fields = [
            'id',
            'rider',
            'created_at',
            'updated_at',
        ]


# =========================================================
# RIDER PROFILE SERIALIZER
# =========================================================

class RiderProfileSerializer(serializers.ModelSerializer):

    username = serializers.CharField(
        source='user.username',
        read_only=True
    )

    first_name = serializers.CharField(
        source='user.first_name',
        read_only=True
    )

    last_name = serializers.CharField(
        source='user.last_name',
        read_only=True
    )

    role = serializers.CharField(
        source='user.role',
        read_only=True
    )

    details = RiderDetailsSerializer(
        read_only=True
    )

    class Meta:

        model = RiderProfile

        fields = [

            'id',

            'username',
            'first_name',
            'last_name',
            'role',

            'stage',

            'profile_picture',
            'national_id_photo',

            'bike_plate_number',
            'national_id_number',
            'rider_phone_number',

            'latitude',
            'longitude',
            'last_location_update',

            'status',
            'is_verified',
            'is_blacklisted',
            'suspicious_activity_score',
            'total_fines',

            'is_online',
            'is_available',

            'created_at',
            'updated_at',

            'details',
        ]

        read_only_fields = [

            'status',
            'is_verified',
            'is_blacklisted',
            'suspicious_activity_score',
            'total_fines',

            'created_at',
            'updated_at',
        ]

    def validate_bike_plate_number(self, value):

        return value.upper()


# =========================================================
# RIDER SELF UPDATE SERIALIZER
# =========================================================

class RiderSelfUpdateSerializer(serializers.ModelSerializer):

    class Meta:

        model = RiderProfile

        fields = [

            'profile_picture',

            'rider_phone_number',

            'latitude',
            'longitude',

            'is_available',
            'is_online',
        ]


# =========================================================
# GUEST RIDER SERIALIZER
# =========================================================

class GuestRiderSerializer(serializers.ModelSerializer):

    username = serializers.CharField(
        source='user.username',
        read_only=True
    )

    first_name = serializers.CharField(
        source='user.first_name',
        read_only=True
    )

    last_name = serializers.CharField(
        source='user.last_name',
        read_only=True
    )

    class Meta:

        model = GuestRider

        fields = '__all__'

        read_only_fields = [

            'is_blacklisted',

            'suspicious_activity_score',

            'total_fines',

            'created_at',

            'updated_at',
        ]