from rest_framework import serializers
from .models import Fine, FineType


class FineTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = FineType
        fields = '__all__'


class FineSerializer(serializers.ModelSerializer):

    issued_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Fine
        fields = '__all__'
        read_only_fields = [
            'issued_by',
            'status',
            'paid_at',
            'payment_reference',
        ]