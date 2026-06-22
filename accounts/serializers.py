import re
import logging
import secrets
from datetime import timedelta

from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.cache import cache
from django.utils import timezone
from django.core.validators import RegexValidator, EmailValidator

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

PUBLIC_ALLOWED_ROLES = {"guest_rider", "rider"}  # Roles users can register with

# =========================================================
# PHONE VALIDATOR
# =========================================================

phone_validator = RegexValidator(
    regex=r'^\+256[0-9]{9}$',
    message='Phone number must be in format: +2567XXXXXXXX'
)

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
# REGISTER SERIALIZER (FIXED - REMOVED ROLE SELECTION)
# =========================================================

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password]
    )
    
    token = serializers.SerializerMethodField()
    
    # Role is now read-only and will be set to guest_rider by default
    role = serializers.CharField(read_only=True)

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
        read_only_fields = ["id", "created_at", "token", "role"]

    def validate_email(self, value):
        """Make email required and validate it"""
        # Email is now required
        if not value:
            raise serializers.ValidationError("Email is required")
        
        # Clean and validate email
        value = value.lower().strip()
        
        # Additional email validation using Django's EmailValidator
        email_validator = EmailValidator()
        try:
            email_validator(value)
        except Exception:
            raise serializers.ValidationError("Enter a valid email address")
        
        # Check if email already exists
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered")
        
        return value

    def validate_phone_number(self, value):
        return normalize_phone(value)
    
    def validate_username(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Username is required")
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already taken")
        return value

    def validate_first_name(self, value):
        if not value:
            raise serializers.ValidationError("First name is required")
        return value

    def validate_last_name(self, value):
        if not value:
            raise serializers.ValidationError("Last name is required")
        return value

    def create(self, validated_data):
        try:
            # Set role to guest_rider by default
            # Only allow guest_rider or rider
            role = validated_data.get("role", "guest_rider")
            if role not in PUBLIC_ALLOWED_ROLES:
                role = "guest_rider"
            
            user = User.objects.create_user(
                first_name=validated_data["first_name"],
                last_name=validated_data["last_name"],
                username=validated_data["username"],
                email=validated_data["email"],  # Now required
                phone_number=validated_data["phone_number"],
                role=role,  # Always guest_rider or rider
                password=validated_data["password"],
            )

            logger.info(
                "User registered | user_id=%s | username=%s | role=%s | email=%s",
                user.id,
                user.username,
                user.role,
                user.email
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
        fields = [
            "id",
            "first_name",
            "last_name",
            "username",
            "email",
            "phone_number",
            "role",
            "is_verified",
            "is_phone_verified",
            "is_email_verified",
            "is_active",
            "created_at",
        ]

# =========================================================
# DYNAMIC ROLE-BASED SERIALIZER
# =========================================================

class DynamicUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"

    def to_representation(self, instance):
        data = super().to_representation(instance)

        try:
            request = self.context.get("request")
            user = getattr(request, "user", None)

            if user and user.role not in PRIVILEGED_ROLES:
                # Remove sensitive fields for non-privileged users
                sensitive_fields = [
                    "is_active", "role", "failed_login_attempts", 
                    "locked_until", "totp_secret", "is_2fa_enabled",
                    "last_login_ip", "last_login_device"
                ]
                for field in sensitive_fields:
                    data.pop(field, None)

            return data

        except Exception:
            logger.exception(
                "DynamicUserSerializer failed | user=%s",
                getattr(user, "id", None)
            )
            return data

# =========================================================
# RIDER SELF UPDATE (FIXED - WITH OTP VERIFICATION)
# =========================================================

class RiderSelfUpdateSerializer(serializers.ModelSerializer):
    new_phone_number = serializers.CharField(
        write_only=True,
        required=False,
        validators=[phone_validator]
    )
    otp_code = serializers.CharField(
        write_only=True,
        required=False,
        max_length=6
    )
    
    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "phone_number",
            "new_phone_number",
            "otp_code",
        ]
    
    def validate_username(self, value):
        if value:
            value = value.strip()
            if User.objects.filter(username=value).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError("Username already taken")
        return value
    
    def validate_email(self, value):
        if value:
            value = value.lower().strip()
            # Validate email format
            email_validator = EmailValidator()
            try:
                email_validator(value)
            except Exception:
                raise serializers.ValidationError("Enter a valid email address")
            
            if User.objects.filter(email=value).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError("Email already registered")
        return value
    
    def validate_phone_number(self, value):
        if value:
            return normalize_phone(value)
        return value
    
    def validate_new_phone_number(self, value):
        if value:
            value = normalize_phone(value)
            if User.objects.filter(phone_number=value).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError("Phone number already registered")
        return value
    
    def validate(self, data):
        # If changing phone number, OTP is required
        if data.get('new_phone_number'):
            otp_code = data.get('otp_code')
            if not otp_code:
                raise serializers.ValidationError({
                    "otp_code": "OTP required to change phone number"
                })
            
            # Verify OTP
            from .utils import verify_otp_code
            if not verify_otp_code(data['new_phone_number'], otp_code, 'phone_change'):
                raise serializers.ValidationError({
                    "otp_code": "Invalid or expired OTP"
                })
        
        return data
    
    def update(self, instance, validated_data):
        # Handle phone number change
        if validated_data.get('new_phone_number'):
            instance.phone_number = validated_data['new_phone_number']
            # Reset verification status - new phone needs re-verification
            instance.is_phone_verified = False
        
        # Update other fields
        if validated_data.get('username'):
            instance.username = validated_data['username']
        if validated_data.get('email'):
            instance.email = validated_data['email']
        instance.save()
        
        return instance

# =========================================================
# OTP SEND SERIALIZER
# =========================================================

class OTPSendSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    purpose = serializers.ChoiceField(
        choices=['verification', 'password_reset', 'phone_change'],
        default='verification'
    )

    def validate_phone_number(self, value):
        return normalize_phone(value)

# =========================================================
# OTP VERIFY SERIALIZER
# =========================================================

class OTPVerificationSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    otp_code = serializers.CharField(max_length=6)
    purpose = serializers.ChoiceField(
        choices=['verification', 'password_reset', 'phone_change'],
        default='verification'
    )

    def validate_phone_number(self, value):
        return normalize_phone(value)

# =========================================================
# PASSWORD RESET REQUEST SERIALIZER
# =========================================================

class PasswordResetRequestSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    
    def validate_phone_number(self, value):
        value = normalize_phone(value)
        if not User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("Phone number not registered")
        return value

# =========================================================
# PASSWORD RESET CONFIRM SERIALIZER (FIXED)
# =========================================================

class PasswordResetConfirmSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    otp_code = serializers.CharField(max_length=6)
    new_password = serializers.CharField(
        write_only=True,
        validators=[validate_password]
    )
    confirm_password = serializers.CharField(write_only=True)

    def validate_phone_number(self, value):
        return normalize_phone(value)
    
    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({
                "confirm_password": "Passwords do not match"
            })
        return data

# =========================================================
# ADMIN ROLE UPDATE SERIALIZER
# =========================================================

class AdminRoleUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['role', 'is_active', 'is_verified']
    
    def validate_role(self, value):
        if value not in dict(User.ROLE_CHOICES).keys():
            raise serializers.ValidationError("Invalid role")
        return value

# =========================================================
# CHANGE PASSWORD SERIALIZER
# =========================================================

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(
        write_only=True,
        validators=[validate_password]
    )
    confirm_password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({
                "confirm_password": "Passwords do not match"
            })
        return data