import logging
from rest_framework import serializers
from .models import AuditLog

logger = logging.getLogger("audit.serializers")


class AuditLogSerializer(serializers.ModelSerializer):

    user_email = serializers.SerializerMethodField()
    user_id = serializers.IntegerField(
        source="user.id",
        read_only=True
    )

    class Meta:
        model = AuditLog

        fields = [
            "id",
            "user_id",
            "user_email",
            "action",
            "entity",
            "entity_id",
            "ip_address",
            "user_agent",
            "request_method",
            "path",
            "metadata",
            "timestamp",
        ]

        read_only_fields = fields  # full audit logs should NEVER be writable

    # =========================================================
    # SAFE USER EMAIL RESOLUTION
    # =========================================================

    def get_user_email(self, obj):
        try:
            if obj.user:
                return obj.user.email
            return None
        except Exception:
            logger.exception(
                "Failed to resolve user_email for AuditLog id=%s",
                getattr(obj, "id", None),
            )
            return None