import logging
from rest_framework import serializers
from .models import Announcement, Condolence

logger = logging.getLogger("announcements.serializers")


# =========================================================
# ANNOUNCEMENT SERIALIZER (PRODUCTION READY)
# =========================================================

class AnnouncementSerializer(serializers.ModelSerializer):

    created_by_email = serializers.EmailField(
        source="created_by.email",
        read_only=True
    )

    class Meta:
        model = Announcement

        fields = [
            "id",
            "title",
            "message",
            "announcement_type",
            "created_by",
            "created_by_email",
            "is_active",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "created_by_email",
            "created_at",
        ]

    def create(self, validated_data):
        try:
            instance = super().create(validated_data)

            logger.info(
                "Announcement created | id=%s | type=%s",
                instance.id,
                instance.announcement_type
            )

            return instance

        except Exception as exc:
            logger.exception("Failed to create announcement")
            raise


# =========================================================
# CONDOLENCE SERIALIZER (PRODUCTION READY)
# =========================================================

class CondolenceSerializer(serializers.ModelSerializer):

    rider_email = serializers.EmailField(
        source="rider.user.email",
        read_only=True
    )

    reported_by_email = serializers.EmailField(
        source="reported_by.email",
        read_only=True
    )

    class Meta:
        model = Condolence

        fields = [
            "id",
            "rider",
            "rider_email",
            "reported_by",
            "reported_by_email",
            "description",
            "burial_location",
            "date_of_death",
            "status",
            "target_role",
            "verified_by",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "rider_email",
            "reported_by_email",
            "created_at",
        ]

    def create(self, validated_data):
        try:
            instance = super().create(validated_data)

            logger.info(
                "Condolence created | id=%s | rider_id=%s | status=%s",
                instance.id,
                instance.rider_id,
                instance.status
            )

            return instance

        except Exception:
            logger.exception("Failed to create condolence")
            raise