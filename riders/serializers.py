import logging
from rest_framework import serializers
from .models import RiderProfile, RiderDetails, GuestRider

logger = logging.getLogger("riders.serializers")


# =========================================================
# RIDER DETAILS SERIALIZER
# =========================================================

class RiderDetailsSerializer(serializers.ModelSerializer):

    class Meta:
        model = RiderDetails

        fields = [
            "id",
            "rider",
            "residence",
            "village_name",
            "landlord_name",
            "landlord_phone",
            "father_name",
            "father_phone",
            "mother_name",
            "mother_phone",
            "wife_name",
            "wife_phone",
            "emergency_contact_name",
            "emergency_contact_phone",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "rider",
            "created_at",
            "updated_at",
        ]


# =========================================================
# RIDER PROFILE SERIALIZER
# =========================================================

class RiderProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = RiderProfile

        fields = [
            "id",
            "user",
            "stage",
            "profile_picture",
            "national_id_photo",
            "bike_plate_number",
            "national_id_number",
            "rider_phone_number",
            "latitude",
            "longitude",
            "last_location_update",
            "status",
            "is_verified",
            "is_blacklisted",
            "suspicious_activity_score",
            "total_fines",
            "is_online",
            "is_available",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "status",
            "is_verified",
            "is_blacklisted",
            "suspicious_activity_score",
            "total_fines",
            "created_at",
            "updated_at",
        ]

    # =====================================================
    # VALIDATION
    # =====================================================

    def validate_bike_plate_number(self, value):
        value = value.upper()
        logger.debug(f"Validating plate number: {value}")
        return value


# =========================================================
# GUEST RIDER SERIALIZER
# =========================================================

class GuestRiderSerializer(serializers.ModelSerializer):

    class Meta:
        model = GuestRider

        fields = [
            "id",
            "user",
            "bike_plate_number",
            "national_id_number",
            "phone_number",
            "current_area",
            "latitude",
            "longitude",
            "last_location_update",
            "status",
            "total_fines",
            "suspicious_activity_score",
            "is_blacklisted",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "status",
            "total_fines",
            "suspicious_activity_score",
            "is_blacklisted",
            "created_at",
            "updated_at",
        ]

    # =====================================================
    # VALIDATION
    # =====================================================

    def validate_bike_plate_number(self, value):
        value = value.upper()
        logger.debug(f"Validating guest plate: {value}")
        return value