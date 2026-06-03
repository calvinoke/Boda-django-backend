from rest_framework import serializers
from .models import Fine, FineType


# =========================================================
# FINE TYPE SERIALIZER
# =========================================================

class FineTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = FineType
        fields = [
            "id",
            "name",
            "description",
            "default_amount",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]


# =========================================================
# FINE SERIALIZER
# =========================================================

class FineSerializer(serializers.ModelSerializer):

    issued_by = serializers.StringRelatedField(
        read_only=True
    )

    class Meta:
        model = Fine

        fields = [
            "id",
            "issued_by",
            "rider",
            "guest_rider",
            "offender_type",
            "fine_type",
            "reason",
            "amount",
            "stage",
            "latitude",
            "longitude",
            "evidence_image",
            "status",
            "paid_at",
            "payment_reference",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "issued_by",
            "status",
            "paid_at",
            "payment_reference",
            "created_at",
            "updated_at",
        ]

    # =====================================================
    # VALIDATION
    # =====================================================

    def validate(self, attrs):

        offender_type = attrs.get("offender_type")

        rider = attrs.get("rider")
        guest_rider = attrs.get("guest_rider")

        if offender_type == "rider":

            if not rider:
                raise serializers.ValidationError(
                    {
                        "rider": (
                            "Rider is required when "
                            "offender_type is 'rider'."
                        )
                    }
                )

            if guest_rider:
                raise serializers.ValidationError(
                    {
                        "guest_rider": (
                            "guest_rider must be empty "
                            "for rider fines."
                        )
                    }
                )

        elif offender_type == "guest_rider":

            if not guest_rider:
                raise serializers.ValidationError(
                    {
                        "guest_rider": (
                            "Guest rider is required when "
                            "offender_type is 'guest_rider'."
                        )
                    }
                )

            if rider:
                raise serializers.ValidationError(
                    {
                        "rider": (
                            "rider must be empty for "
                            "guest rider fines."
                        )
                    }
                )

        return attrs

    # =====================================================
    # AMOUNT VALIDATION
    # =====================================================

    def validate_amount(self, value):

        if value < 0:
            raise serializers.ValidationError(
                "Amount cannot be negative."
            )

        return value