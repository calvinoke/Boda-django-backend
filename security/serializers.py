from rest_framework import serializers
from .models import SecurityAlert


class SecurityAlertSerializer(serializers.ModelSerializer):

    username = serializers.CharField(
        source='user.username',
        read_only=True
    )

    class Meta:

        model = SecurityAlert

        fields = '__all__'

        read_only_fields = [

            'created_at',

            'updated_at',

            'resolved_by',

            'resolved_at',
        ]