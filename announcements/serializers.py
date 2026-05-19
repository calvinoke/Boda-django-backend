from rest_framework import serializers
from .models import (Announcement,Condolence)


class AnnouncementSerializer(
    serializers.ModelSerializer
):

    created_by_email = serializers.EmailField(
        source='created_by.email',
        read_only=True
    )

    class Meta:

        model = Announcement

        fields = '__all__'


class CondolenceSerializer(
    serializers.ModelSerializer
):

    rider_email = serializers.EmailField(
        source='rider.user.email',
        read_only=True
    )

    reported_by_email = serializers.EmailField(
        source='reported_by.email',
        read_only=True
    )

    class Meta:

        model = Condolence

        fields = '__all__'