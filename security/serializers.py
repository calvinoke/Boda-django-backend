from rest_framework import serializers
from .models import SecurityAlert


# =========================================================
# SECURITY ALERT SERIALIZER
# =========================================================

class SecurityAlertSerializer(serializers.ModelSerializer):

    username = serializers.CharField(
        source="user.username",
        read_only=True,
    )

    resolved_by_username = serializers.CharField(
        source="resolved_by.username",
        read_only=True,
    )

    class Meta:

        model = SecurityAlert

        fields = [
            "id",
            "user",
            "username",
            "alert_type",
            "reason",
            "severity",
            "auto_flagged",
            "resolved",
            "resolved_by",
            "resolved_by_username",
            "resolved_at",
            "resolution_notes",
            "ip_address",
            "device_info",
            "latitude",
            "longitude",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "resolved_by",
            "resolved_at",
            "username",
            "resolved_by_username",
        ]

    # =====================================================
    # VALIDATION
    # =====================================================

    def validate(self, attrs):

        severity = attrs.get("severity")

        if severity not in {
            "low",
            "medium",
            "high",
            "critical",
        }:
            raise serializers.ValidationError(
                {"severity": "Invalid severity value."}
            )

        return attrs