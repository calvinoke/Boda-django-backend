from rest_framework import serializers
from .models import EmergencyContact


class EmergencyContactSerializer(
    serializers.ModelSerializer
):

    rider_name = serializers.CharField(
        source='rider.user.username',
        read_only=True
    )

    class Meta:

        model = EmergencyContact

        fields = '__all__'

        read_only_fields = [

            'rider',

            'created_at',

            'updated_at'
        ]