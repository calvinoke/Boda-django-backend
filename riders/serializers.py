from rest_framework import serializers
from .models import RiderProfile

class RiderProfileSerializer(serializers.ModelSerializer):

    email = serializers.EmailField(source='user.email', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    phone_number = serializers.CharField(source='user.phone_number', read_only=True)

    class Meta:
        model = RiderProfile

        fields = [

            'id',

            'email',

            'username',

            'phone_number',

            'bike_plate_number',

            'national_id_number',

            'stage_name',

            'residence',

            'village_name',

            'status',

            'is_online',

            'is_available',

            'created_at',
        ]

        read_only_fields = [
            'status',
            'is_online',
            'is_available',
        ]

    def validate_bike_plate_number(self, value):

        return value.upper()