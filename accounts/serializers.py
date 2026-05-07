from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User

class RegisterSerializer(serializers.ModelSerializer):

    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )

    class Meta:
        model = User
        fields = [
            'email',
            'username',
            'phone_number',
            'password',
        ]

    def create(self, validated_data):

        user = User.objects.create_user(
            email=validated_data['email'].lower(),
            username=validated_data['username'],
            phone_number=validated_data['phone_number'],
            password=validated_data['password']
        )

        return user