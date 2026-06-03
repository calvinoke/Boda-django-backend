import re
import logging

from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

logger = logging.getLogger("accounts.serializers")

User = get_user_model()


# =========================================================
# CONSTANTS (ROLE SECURITY)
# =========================================================

PRIVILEGED_ROLES = {
    "super_admin",
    "stage_chairman",
    "stage_secretary",
    "stage_defense",
}


# =========================================================
# PHONE NORMALIZATION
# =========================================================

def normalize_phone(phone):
    try:
        if not phone:
            raise serializers.ValidationError("Phone number is required.")

        phone = phone.strip()

        # 07XXXXXXXX → +2567XXXXXXXX
        if re.match(r"^0[0-9]{9}$", phone):
            normalized = "+256" + phone[1:]
            logger.debug("Phone normalized local format -> %s", normalized)
            return normalized

        # Already international format
        if re.match(r"^\+256[0-9]{9}$", phone):
            logger.debug("Phone already normalized -> %s", phone)
            return phone

        raise serializers.ValidationError(
            "Invalid phone format. Use 07XXXXXXXX or +2567XXXXXXXX"
        )

    except Exception:
        logger.exception("Phone normalization failed | value=%s", phone)
        raise


# =========================================================
# JWT TOKEN GENERATOR
# =========================================================

def get_tokens_for_user(user):
    try:
        refresh = RefreshToken.for_user(user)

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }

    except Exception:
        logger.exception("JWT generation failed | user=%s", user)
        raise


# =========================================================
# REGISTER SERIALIZER
# =========================================================

class RegisterSerializer(serializers.ModelSerializer):

    password = serializers.CharField(
        write_only=True,
        validators=[validate_password]
    )

    token = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "username",
            "email",
            "phone_number",
            "role",
            "password",
            "token",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "token"]

    def validate_phone_number(self, value):
        return normalize_phone(value)

    def create(self, validated_data):
        try:
            user = User.objects.create_user(
                first_name=validated_data["first_name"],
                last_name=validated_data["last_name"],
                username=validated_data["username"],
                email=validated_data.get("email"),
                phone_number=validated_data["phone_number"],
                role=validated_data.get("role", "guest_rider"),
                password=validated_data["password"],
            )

            logger.info(
                "User registered | user_id=%s | username=%s",
                user.id,
                user.username
            )

            return user

        except Exception:
            logger.exception("User registration failed | data=%s", validated_data)
            raise

    def get_token(self, user):
        return get_tokens_for_user(user)


# =========================================================
# USER SERIALIZER (SAFE - NO __ALL__)
# =========================================================

class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User

        # ❌ NEVER USE "__all__" IN AUTH MODELS
        fields = [
            "id",
            "first_name",
            "last_name",
            "username",
            "email",
            "phone_number",
            "role",
            "is_verified",
            "is_active",
            "created_at",
        ]


# =========================================================
# DYNAMIC ROLE-BASED SERIALIZER
# =========================================================

class DynamicUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User

        # ⚠️ allowed but controlled via to_representation
        fields = "__all__"

    def to_representation(self, instance):
        data = super().to_representation(instance)

        try:
            request = self.context.get("request")
            user = getattr(request, "user", None)

            if user and user.role not in PRIVILEGED_ROLES:
                data.pop("is_active", None)
                data.pop("role", None)

            return data

        except Exception:
            logger.exception(
                "DynamicUserSerializer failed | user=%s",
                getattr(user, "id", None)
            )
            return data


# =========================================================
# RIDER SELF UPDATE
# =========================================================

class RiderSelfUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "phone_number",
        ]

    def validate_phone_number(self, value):
        return normalize_phone(value)


# =========================================================
# OTP SERIALIZERS
# =========================================================

class OTPVerificationSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    otp_code = serializers.CharField(max_length=6)

    def validate_phone_number(self, value):
        return normalize_phone(value)


class PasswordResetRequestSerializer(serializers.Serializer):
    phone_number = serializers.CharField()

    def validate_phone_number(self, value):
        return normalize_phone(value)


class PasswordResetConfirmSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    otp_code = serializers.CharField(max_length=6)
    new_password = serializers.CharField(
        write_only=True,
        validators=[validate_password]
    )

    def validate_phone_number(self, value):
        return normalize_phone(value)