import logging
from rest_framework import serializers
from .models import Stage
from accounts.serializers import UserSerializer

logger = logging.getLogger("stages.serializers")


# =========================================================
# READ SERIALIZER (SAFE OUTPUT)
# =========================================================

class StageSerializer(serializers.ModelSerializer):

    chairman = UserSerializer(read_only=True)
    secretary = UserSerializer(read_only=True)
    defense = UserSerializer(read_only=True)

    class Meta:
        model = Stage

        fields = [
            "id",
            "name",
            "district",
            "division",
            "parish",
            "village",
            "chairman",
            "secretary",
            "defense",
            "chairman_phone",
            "secretary_phone",
            "defense_phone",
            "latitude",
            "longitude",
            "is_active",
            "total_registered_riders",
            "total_guest_riders_seen",
            "suspicious_activity_score",
            "created_at",
            "updated_at",
        ]


# =========================================================
# CREATE / UPDATE SERIALIZER (CONTROLLED WRITE)
# =========================================================

class StageCreateUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Stage

        fields = [
            "id",
            "name",
            "district",
            "division",
            "parish",
            "village",
            "chairman",
            "secretary",
            "defense",
            "chairman_phone",
            "secretary_phone",
            "defense_phone",
            "latitude",
            "longitude",
            "is_active",
        ]

        read_only_fields = [
            "total_registered_riders",
            "total_guest_riders_seen",
            "suspicious_activity_score",
        ]

    # =====================================================
    # VALIDATION LAYER (PRODUCTION SAFETY)
    # =====================================================

    def validate(self, data):

        # Ensure no duplicate logical assignment errors
        chairman = data.get("chairman")
        secretary = data.get("secretary")
        defense = data.get("defense")

        if chairman and secretary and chairman == secretary:
            raise serializers.ValidationError(
                "Chairman and Secretary cannot be the same user."
            )

        if chairman and defense and chairman == defense:
            raise serializers.ValidationError(
                "Chairman and Defense cannot be the same user."
            )

        if secretary and defense and secretary == defense:
            raise serializers.ValidationError(
                "Secretary and Defense cannot be the same user."
            )

        return data

    # =====================================================
    # OPTIONAL LOGGING (DEBUGGING / AUDIT)
    # =====================================================

    def create(self, validated_data):
        instance = super().create(validated_data)
        logger.info(f"Stage created via serializer | id={instance.id}")
        return instance

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        logger.info(f"Stage updated via serializer | id={instance.id}")
        return instance