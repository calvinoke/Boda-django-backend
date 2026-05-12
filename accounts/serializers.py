from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password

from .models import User


# =========================================================
# REGISTER SERIALIZER
# =========================================================

class RegisterSerializer(serializers.ModelSerializer):

    password = serializers.CharField(
        write_only=True,
        validators=[validate_password]
    )

    class Meta:

        model = User

        fields = [

            'id',

            'first_name',

            'last_name',

            'username',

            'phone_number',

            'role',

            'password',

            'created_at',
        ]

        read_only_fields = [

            'id',

            'created_at',
        ]

    def create(self, validated_data):

        user = User.objects.create_user(

            first_name=validated_data['first_name'],

            last_name=validated_data['last_name'],

            username=validated_data['username'],

            phone_number=validated_data['phone_number'],

            role=validated_data.get('role', 'guest_rider'),

            password=validated_data['password']
        )

        return user


# =========================================================
# USER SERIALIZER
# =========================================================

class UserSerializer(serializers.ModelSerializer):

    class Meta:

        model = User

        fields = [

            'id',

            'first_name',

            'last_name',

            'username',

            'phone_number',

            'role',

            'is_verified',

            'is_active',

            'created_at',
        ]


# =========================================================
# RIDER SELF UPDATE
# =========================================================

class RiderSelfUpdateSerializer(serializers.ModelSerializer):

    class Meta:

        model = User

        fields = [

            'username',

            'phone_number',
        ]