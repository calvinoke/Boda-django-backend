from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):

    # =====================================================
    # OPTIONAL UI HELPERS (READ-ONLY)
    # =====================================================

    is_unread = serializers.SerializerMethodField()

    def get_is_unread(self, obj):
        return not obj.is_read

    # =====================================================
    # META CONFIG
    # =====================================================

    class Meta:

        model = Notification

        fields = [
            "id",
            "user",
            "title",
            "message",
            "notification_type",
            "is_read",
            "is_unread",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "user",
            "created_at",
            "is_read",
        ]

    # =====================================================
    # VALIDATION
    # =====================================================

    def validate_title(self, value):
        if not value or len(value.strip()) < 3:
            raise serializers.ValidationError("Title is too short")
        return value

    def validate_message(self, value):
        if not value or len(value.strip()) < 5:
            raise serializers.ValidationError("Message is too short")
        return value