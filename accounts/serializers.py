import re
from rest_framework import serializers
from django.contrib.auth.password_validation import (validate_password)
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import (RefreshToken)


User = get_user_model()


# =========================================================
# PHONE NORMALIZATION
# =========================================================

def normalize_phone(phone):

    """
    ACCEPTS:

    0772123456
    +256772123456

    STORES:

    +256772123456
    """

    if not phone:

        raise serializers.ValidationError(
            "Phone number is required."
        )

    phone = phone.strip()

    # =====================================================
    # 07XXXXXXXX
    # =====================================================

    if re.match(r'^0[0-9]{9}$', phone):

        return '+256' + phone[1:]

    # =====================================================
    # +256XXXXXXXXX
    # =====================================================

    if re.match(r'^\+256[0-9]{9}$', phone):

        return phone

    # =====================================================
    # INVALID FORMAT
    # =====================================================

    raise serializers.ValidationError(

        "Invalid phone format. "
        "Use 07XXXXXXXX or +2567XXXXXXXX"
    )


# =========================================================
# JWT TOKEN GENERATOR
# =========================================================

def get_tokens_for_user(user):

    refresh = RefreshToken.for_user(user)

    return {

        'refresh': str(refresh),

        'access': str(refresh.access_token),
    }


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

            'id',

            'first_name',

            'last_name',

            'username',

            'email',

            'phone_number',

            'role',

            'password',

            'token',

            'created_at',
        ]

        read_only_fields = [

            'id',

            'created_at',

            'token',
        ]

    # =====================================================
    # PHONE NORMALIZATION
    # =====================================================

    def validate_phone_number(self,value):

        return normalize_phone(value)

    # =====================================================
    # CREATE USER
    # =====================================================

    def create( self, validated_data):

        user = User.objects.create_user(

            first_name=validated_data[
                'first_name'
            ],

            last_name=validated_data[
                'last_name'
            ],

            username=validated_data[
                'username'
            ],

            email=validated_data.get(
                'email'
            ),

            phone_number=validated_data[
                'phone_number'
            ],

            role=validated_data.get(
                'role',
                'guest_rider'
            ),

            password=validated_data[
                'password'
            ]
        )

        return user

    # =====================================================
    # JWT TOKEN RESPONSE
    # =====================================================

    def get_token(self, user):

        return get_tokens_for_user(user)


# =========================================================
# USER SERIALIZER
# =========================================================

class UserSerializer( serializers.ModelSerializer):

    class Meta:

        model = User

        fields = [

            'id',

            'first_name',

            'last_name',

            'username',

            'email',

            'phone_number',

            'role',

            'is_verified',

            'is_active',

            'created_at',
        ]


# =========================================================
# DYNAMIC ROLE-BASED SERIALIZER
# =========================================================

class DynamicUserSerializer(serializers.ModelSerializer):

    class Meta:

        model = User

        fields = '__all__'

    def to_representation(self,instance):

        data = super().to_representation( instance)

        request = self.context.get('request')

        user = (
            request.user
            if request else None
        )

        # =================================================
        # HIDE SENSITIVE FIELDS
        # =================================================

        if user and user.role not in [

            'super_admin',

            'stage_chairman',

            'stage_secretary',

            'stage_defense'
        ]:

            data.pop('is_active', None)

            data.pop('role', None)

        return data


# =========================================================
# RIDER SELF UPDATE
# =========================================================

class RiderSelfUpdateSerializer(serializers.ModelSerializer):

    class Meta:

        model = User

        fields = [

            'username',

            'email',

            'phone_number',
        ]

    def validate_phone_number( self, value):

        return normalize_phone(value)


# =========================================================
# OTP VERIFICATION
# =========================================================

class OTPVerificationSerializer(serializers.Serializer):

    phone_number = serializers.CharField()

    otp_code = serializers.CharField( max_length=6)

    def validate_phone_number( self,value):

        return normalize_phone(value)


# =========================================================
# PASSWORD RESET REQUEST
# =========================================================

class PasswordResetRequestSerializer(serializers.Serializer):

    phone_number = serializers.CharField()

    def validate_phone_number(self,value):

        return normalize_phone(value)


# =========================================================
# PASSWORD RESET CONFIRM
# =========================================================

class PasswordResetConfirmSerializer(serializers.Serializer):

    phone_number = serializers.CharField()

    otp_code = serializers.CharField(max_length=6)

    new_password = serializers.CharField( write_only=True, validators=[validate_password])

    def validate_phone_number(self,value):

        return normalize_phone(value)