from rest_framework import serializers
from .models import RiderLocation, SuspiciousEvent


# =========================================================
# RIDER LOCATION SERIALIZER
# =========================================================

class RiderLocationSerializer(serializers.ModelSerializer):

    rider_name = serializers.SerializerMethodField()
    guest_rider_name = serializers.SerializerMethodField()

    class Meta:
        model = RiderLocation

        fields = [
            "id",
            "rider",
            "guest_rider",
            "rider_name",
            "guest_rider_name",
            "latitude",
            "longitude",
            "speed",
            "heading",
            "is_suspicious",
            "detected_violation",
            "recorded_at",
        ]

        read_only_fields = [
            "is_suspicious",
            "detected_violation",
            "recorded_at",
        ]

    # =====================================================
    # SAFE USERNAME RESOLUTION
    # =====================================================

    def get_rider_name(self, obj):
        try:
            return obj.rider.user.username if obj.rider else None
        except Exception:
            return None

    def get_guest_rider_name(self, obj):
        try:
            return obj.guest_rider.user.username if obj.guest_rider else None
        except Exception:
            return None

    # =====================================================
    # VALIDATION RULES
    # =====================================================

    def validate(self, data):

        rider = data.get("rider")
        guest_rider = data.get("guest_rider")

        if not rider and not guest_rider:
            raise serializers.ValidationError(
                "Either rider or guest_rider must be provided."
            )

        if rider and guest_rider:
            raise serializers.ValidationError(
                "Cannot assign both rider and guest_rider."
            )

        return data


# =========================================================
# SUSPICIOUS EVENT SERIALIZER
# =========================================================

class SuspiciousEventSerializer(serializers.ModelSerializer):

    rider_name = serializers.SerializerMethodField()
    guest_rider_name = serializers.SerializerMethodField()

    class Meta:
        model = SuspiciousEvent

        fields = [
            "id",
            "rider",
            "guest_rider",
            "rider_name",
            "guest_rider_name",
            "event_type",
            "description",
            "latitude",
            "longitude",
            "auto_fine_triggered",
            "created_at",
        ]

        read_only_fields = [
            "auto_fine_triggered",
            "created_at",
        ]

    # =====================================================
    # SAFE NAME ACCESS
    # =====================================================

    def get_rider_name(self, obj):
        try:
            return obj.rider.user.username if obj.rider else None
        except Exception:
            return None

    def get_guest_rider_name(self, obj):
        try:
            return obj.guest_rider.user.username if obj.guest_rider else None
        except Exception:
            return None

    # =====================================================
    # VALIDATION RULES
    # =====================================================

    def validate(self, data):

        rider = data.get("rider")
        guest_rider = data.get("guest_rider")

        if not rider and not guest_rider:
            raise serializers.ValidationError(
                "Event must belong to either rider or guest_rider."
            )

        if rider and guest_rider:
            raise serializers.ValidationError(
                "Event cannot belong to both rider and guest_rider."
            )

        return data