from rest_framework import serializers
from .models import (

    RiderActivity,

    SystemLog
)


class RiderActivitySerializer(

    serializers.ModelSerializer
):

    rider_email = serializers.EmailField(

        source='rider.user.email',

        read_only=True
    )

    class Meta:

        model = RiderActivity

        fields = '__all__'


class SystemLogSerializer(

    serializers.ModelSerializer
):

    class Meta:

        model = SystemLog

        fields = '__all__'