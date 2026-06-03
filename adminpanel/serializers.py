import logging
from rest_framework import serializers
from .models import RiderActivity, SystemLog

logger = logging.getLogger("activity.serializers")


# =========================================================
# RIDER ACTIVITY SERIALIZER
# =========================================================

class RiderActivitySerializer(serializers.ModelSerializer):

    rider_email = serializers.SerializerMethodField()

    class Meta:
        model = RiderActivity

        # ❌ DO NOT USE "__all__" IN PRODUCTION AUDIT MODELS
        fields = [
            "id",
            "rider",
            "rider_email",
            "action",
            "description",
            "timestamp",
        ]

        read_only_fields = [
            "id",
            "timestamp",
            "rider_email",
        ]

    def get_rider_email(self, obj):
        try:
            return obj.rider.user.email
        except Exception:
            logger.warning(
                "Failed to resolve rider email | rider_id=%s",
                getattr(obj.rider, "id", None)
            )
            return None


# =========================================================
# SYSTEM LOG SERIALIZER (READ-ONLY SAFETY)
# =========================================================

class SystemLogSerializer(serializers.ModelSerializer):

    class Meta:
        model = SystemLog

        # SECURITY: system logs should NOT be writable via API
        fields = [
            "id",
            "message",
            "level",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
        ]

    def create(self, validated_data):
        """
        Optional safety layer:
        Prevent external creation unless explicitly allowed.
        """
        logger.warning(
            "Attempt to create SystemLog via API | data=%s",
            validated_data
        )
        return super().create(validated_data)