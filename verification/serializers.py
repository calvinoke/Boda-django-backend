import logging
from rest_framework import serializers
from .models import RiderVerification, VerificationRequest


logger = logging.getLogger("verification.serializers")


# =========================================================
# RIDER VERIFICATION SERIALIZER
# =========================================================

class RiderVerificationSerializer(serializers.ModelSerializer):

    rider_username = serializers.SerializerMethodField()
    verified_by_username = serializers.SerializerMethodField()

    class Meta:
        model = RiderVerification

        fields = [
            "id",
            "rider",
            "rider_username",
            "national_id_front",
            "national_id_back",
            "driving_license",
            "passport_photo",
            "police_clearance",
            "is_verified",
            "verified_by",
            "verified_by_username",
            "verified_at",
            "submitted_at",
            "updated_at",
        ]

        read_only_fields = [
            "is_verified",
            "verified_by",
            "verified_at",
            "submitted_at",
            "updated_at",
        ]

    # =====================================================
    # SAFE FIELD RESOLVERS
    # =====================================================

    def get_rider_username(self, obj):
        try:
            return obj.rider.user.username if obj.rider and obj.rider.user else None
        except Exception as e:
            logger.warning(f"rider_username resolve failed: {e}")
            return None

    def get_verified_by_username(self, obj):
        try:
            return obj.verified_by.username if obj.verified_by else None
        except Exception as e:
            logger.warning(f"verified_by_username resolve failed: {e}")
            return None

    # =====================================================
    # VALIDATION RULES
    # =====================================================

    def validate(self, data):

        rider = data.get("rider")

        if not rider:
            raise serializers.ValidationError(
                "Rider is required for verification."
            )

        return data


# =========================================================
# VERIFICATION REQUEST SERIALIZER
# =========================================================

class VerificationRequestSerializer(serializers.ModelSerializer):

    username = serializers.SerializerMethodField()

    class Meta:
        model = VerificationRequest

        fields = [
            "id",
            "user",
            "username",
            "submitted_by",
            "status",
            "notes",
            "created_at",
        ]

        read_only_fields = [
            "created_at",
            "status",
        ]

    # =====================================================
    # SAFE USERNAME ACCESS
    # =====================================================

    def get_username(self, obj):
        try:
            return obj.user.username if obj.user else None
        except Exception as e:
            logger.warning(f"username resolve failed: {e}")
            return None

    # =====================================================
    # VALIDATION RULES
    # =====================================================

    def validate(self, data):

        user = data.get("user")

        if not user:
            raise serializers.ValidationError(
                "User is required for verification request."
            )

        return data