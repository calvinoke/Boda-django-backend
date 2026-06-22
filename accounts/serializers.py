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

PUBLIC_ALLOWED_ROLES = {"guest_rider", "rider"}

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
    """
    Normalize phone number to international format.
    
    Args:
        phone (str): Phone number to normalize
    
    Returns:
        str: Normalized phone number
    
    Raises:
        serializers.ValidationError: If phone number is invalid
    """
    try:
        if not phone:
            raise serializers.ValidationError("Phone number is required.")

        phone = phone.strip()

        # 07XXXXXXXX → +2567XXXXXXXX
        if re.match(r"^0[0-9]{9}$", phone):
            normalized = "+256" + phone[1:]
            logger.debug(
                "Phone normalized local format -> %s",
                normalized,
                extra={"original": phone, "normalized": normalized}
            )
            return normalized

        # Already international format
        if re.match(r"^\+256[0-9]{9}$", phone):
            logger.debug(
                "Phone already normalized -> %s",
                phone,
                extra={"phone": phone}
            )
            return phone

        raise serializers.ValidationError(
            "Invalid phone format. Use 07XXXXXXXX or +2567XXXXXXXX"
        )

    except serializers.ValidationError:
        raise
    except Exception as e:
        logger.exception(
            "Phone normalization failed | value=%s | error=%s",
            phone,
            str(e)
        )
        raise serializers.ValidationError("Phone number normalization failed")

# =========================================================
# JWT TOKEN GENERATOR
# =========================================================

def get_tokens_for_user(user):
    """
    Generate JWT tokens for a user.
    
    Args:
        user: User object
    
    Returns:
        dict: Dictionary containing refresh and access tokens
    """
    try:
        refresh = RefreshToken.for_user(user)

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }

    except Exception as e:
        logger.exception(
            "JWT generation failed | user=%s | error=%s",
            user.username,
            str(e)
        )
        raise serializers.ValidationError("Token generation failed")

# =========================================================
# REGISTER SERIALIZER
# =========================================================

class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    Users are created with 'guest_rider' role by default.
    """
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        help_text="Password must be at least 8 characters"
    )
    
    token = serializers.SerializerMethodField(
        help_text="JWT tokens for immediate login"
    )
    role = serializers.CharField(
        read_only=True,
        help_text="Role is automatically set to 'guest_rider'"
    )

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
        """
        Validate and normalize email.
        Email is required and must be unique.
        """
        if not value:
            raise serializers.ValidationError("Email is required")
        
        value = value.lower().strip()
        
        # Validate email format
        email_validator = EmailValidator()
        try:
            email_validator(value)
        except Exception:
            raise serializers.ValidationError("Enter a valid email address")
        
        # Check uniqueness
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered")
        
        return value

    def validate_phone_number(self, value):
        """Validate and normalize phone number."""
        return normalize_phone(value)
    
    def validate_username(self, value):
        """Validate username for uniqueness and format."""
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Username is required")
        
        # Check for invalid characters
        if not re.match(r'^[\w.@+-]+$', value):
            raise serializers.ValidationError(
                "Username contains invalid characters"
            )
        
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already taken")
        return value

    def validate_first_name(self, value):
        """Validate first name."""
        if not value:
            raise serializers.ValidationError("First name is required")
        if len(value) < 2:
            raise serializers.ValidationError(
                "First name must be at least 2 characters"
            )
        return value.strip()

    def validate_last_name(self, value):
        """Validate last name."""
        if not value:
            raise serializers.ValidationError("Last name is required")
        if len(value) < 2:
            raise serializers.ValidationError(
                "Last name must be at least 2 characters"
            )
        return value.strip()

    def create(self, validated_data):
        """
        Create a new user with guest_rider role.
        """
        try:
            user = User.objects.create_user(
                first_name=validated_data["first_name"],
                last_name=validated_data["last_name"],
                username=validated_data["username"],
                email=validated_data["email"],
                phone_number=validated_data["phone_number"],
                role="guest_rider",
                password=validated_data["password"],
            )

            logger.info(
                "User registered successfully",
                extra={
                    "user_id": user.id,
                    "username": user.username,
                    "role": user.role,
                    "email": user.email,
                    "phone": user.phone_number
                }
            )

            return user

        except Exception as e:
            logger.exception(
                "User registration failed | data=%s | error=%s",
                {k: v for k, v in validated_data.items() if k != 'password'},
                str(e)
            )
            raise serializers.ValidationError("Registration failed")

    def get_token(self, user):
        """Get JWT tokens for the newly created user."""
        return get_tokens_for_user(user)

# =========================================================
# USER SERIALIZER
# =========================================================

class UserSerializer(serializers.ModelSerializer):
    """
    Basic user serializer with limited fields.
    """
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
        read_only_fields = ["id", "created_at"]

# =========================================================
# DYNAMIC ROLE-BASED SERIALIZER
# =========================================================

class DynamicUserSerializer(serializers.ModelSerializer):
    """
    Dynamic serializer that shows/hides fields based on user role.
    """
    class Meta:
        model = User
        fields = "__all__"

    def to_representation(self, instance):
        data = super().to_representation(instance)

        try:
            request = self.context.get("request")
            user = getattr(request, "user", None)

            # Non-privileged users get limited fields
            if user and user.role not in PRIVILEGED_ROLES:
                sensitive_fields = [
                    "is_active",
                    "role",
                    "failed_login_attempts",
                    "locked_until",
                    "totp_secret",
                    "is_2fa_enabled",
                    "last_login_ip",
                    "last_login_device",
                    "is_superuser",
                    "is_staff"
                ]
                for field in sensitive_fields:
                    data.pop(field, None)

            return data

        except Exception as e:
            logger.exception(
                "DynamicUserSerializer failed | user=%s | error=%s",
                getattr(user, "id", None),
                str(e)
            )
            return data

# =========================================================
# RIDER SELF UPDATE SERIALIZER
# =========================================================

class RiderSelfUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for riders to update their own profile.
    Requires OTP verification for phone number changes.
    """
    new_phone_number = serializers.CharField(
        write_only=True,
        required=False,
        validators=[phone_validator],
        help_text="New phone number (requires OTP verification)"
    )
    otp_code = serializers.CharField(
        write_only=True,
        required=False,
        max_length=6,
        help_text="OTP code for phone number change"
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
        """Validate username update."""
        if value:
            value = value.strip()
            if not re.match(r'^[\w.@+-]+$', value):
                raise serializers.ValidationError(
                    "Username contains invalid characters"
                )
            if User.objects.filter(username=value).exclude(
                id=self.instance.id
            ).exists():
                raise serializers.ValidationError("Username already taken")
        return value
    
    def validate_email(self, value):
        """Validate email update."""
        if value:
            value = value.lower().strip()
            email_validator = EmailValidator()
            try:
                email_validator(value)
            except Exception:
                raise serializers.ValidationError("Enter a valid email address")
            
            if User.objects.filter(email=value).exclude(
                id=self.instance.id
            ).exists():
                raise serializers.ValidationError("Email already registered")
        return value
    
    def validate_phone_number(self, value):
        """Validate current phone number."""
        if value:
            return normalize_phone(value)
        return value
    
    def validate_new_phone_number(self, value):
        """Validate new phone number."""
        if value:
            value = normalize_phone(value)
            if User.objects.filter(phone_number=value).exclude(
                id=self.instance.id
            ).exists():
                raise serializers.ValidationError(
                    "Phone number already registered"
                )
        return value
    
    def validate(self, data):
        """Validate OTP for phone number change."""
        if data.get('new_phone_number'):
            otp_code = data.get('otp_code')
            if not otp_code:
                raise serializers.ValidationError({
                    "otp_code": "OTP required to change phone number"
                })
            
            from .utils import verify_otp_code
            if not verify_otp_code(data['new_phone_number'], otp_code, 'phone_change'):
                raise serializers.ValidationError({
                    "otp_code": "Invalid or expired OTP"
                })
        
        return data
    
    def update(self, instance, validated_data):
        """Update user instance."""
        # Handle phone number change
        if validated_data.get('new_phone_number'):
            instance.phone_number = validated_data['new_phone_number']
            instance.is_phone_verified = False
        
        # Update other fields
        if validated_data.get('username'):
            instance.username = validated_data['username']
        if validated_data.get('email'):
            instance.email = validated_data['email']
        
        instance.save()
        
        logger.info(
            "Rider self-updated",
            extra={
                "user_id": instance.id,
                "username": instance.username,
                "updated_fields": list(validated_data.keys())
            }
        )
        
        return instance

# =========================================================
# ADMIN ROLE UPDATE SERIALIZER
# =========================================================

class AdminRoleUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for admins to update user roles and verification status.
    """
    class Meta:
        model = User
        fields = [
            'role',
            'is_active',
            'is_verified',
            'is_phone_verified',
            'is_email_verified'
        ]
    
    def validate_role(self, value):
        """Validate role assignment."""
        if value not in dict(User.ROLE_CHOICES).keys():
            raise serializers.ValidationError("Invalid role")
        return value
    
    def update(self, instance, validated_data):
        """Update user with role change logging."""
        old_role = instance.role
        instance = super().update(instance, validated_data)
        
        if old_role != instance.role:
            logger.info(
                "Role updated by admin",
                extra={
                    "user_id": instance.id,
                    "username": instance.username,
                    "old_role": old_role,
                    "new_role": instance.role
                }
            )
        
        return instance

# =========================================================
# OTP SEND SERIALIZER
# =========================================================

class OTPSendSerializer(serializers.Serializer):
    """
    Serializer for OTP send requests.
    """
    phone_number = serializers.CharField(
        help_text="Phone number to send OTP to"
    )
    purpose = serializers.ChoiceField(
        choices=['verification', 'password_reset', 'phone_change'],
        default='verification',
        help_text="Purpose of OTP"
    )

    def validate_phone_number(self, value):
        """Validate and normalize phone number."""
        return normalize_phone(value)

# =========================================================
# OTP VERIFY SERIALIZER
# =========================================================

class OTPVerificationSerializer(serializers.Serializer):
    """
    Serializer for OTP verification requests.
    """
    phone_number = serializers.CharField(
        help_text="Phone number to verify OTP for"
    )
    otp_code = serializers.CharField(
        max_length=6,
        help_text="6-digit OTP code"
    )
    purpose = serializers.ChoiceField(
        choices=['verification', 'password_reset', 'phone_change'],
        default='verification',
        help_text="Purpose of OTP"
    )

    def validate_phone_number(self, value):
        """Validate and normalize phone number."""
        return normalize_phone(value)

# =========================================================
# PASSWORD RESET REQUEST SERIALIZER
# =========================================================

class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializer for password reset requests.
    """
    phone_number = serializers.CharField(
        help_text="Phone number associated with the account"
    )
    
    def validate_phone_number(self, value):
        """Validate phone number and check if user exists."""
        value = normalize_phone(value)
        if not User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("Phone number not registered")
        return value

# =========================================================
# PASSWORD RESET CONFIRM SERIALIZER
# =========================================================

class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for password reset confirmation.
    """
    phone_number = serializers.CharField(
        help_text="Phone number associated with the account"
    )
    otp_code = serializers.CharField(
        max_length=6,
        help_text="6-digit OTP code"
    )
    new_password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        help_text="New password"
    )
    confirm_password = serializers.CharField(
        write_only=True,
        help_text="Confirm new password"
    )

    def validate_phone_number(self, value):
        """Validate and normalize phone number."""
        return normalize_phone(value)
    
    def validate(self, data):
        """Validate that passwords match."""
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({
                "confirm_password": "Passwords do not match"
            })
        return data

# =========================================================
# CHANGE PASSWORD SERIALIZER
# =========================================================

class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for password change requests.
    """
    old_password = serializers.CharField(
        write_only=True,
        help_text="Current password"
    )
    new_password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        help_text="New password"
    )
    confirm_password = serializers.CharField(
        write_only=True,
        help_text="Confirm new password"
    )
    
    def validate(self, data):
        """Validate that passwords match."""
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({
                "confirm_password": "Passwords do not match"
            })
        return data