from rest_framework import serializers
from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):

    user_email = serializers.SerializerMethodField()
    user_id = serializers.IntegerField(
        source='user.id',
        read_only=True
    )

    class Meta:
        model = AuditLog

        fields = [
            'id',
            'user_id',
            'user_email',
            'action',
            'entity',
            'entity_id',
            'ip_address',
            'user_agent',
            'metadata',
            'created_at',
        ]

        read_only_fields = fields

    def get_user_email(self, obj):
        """
        Safe access to user email (prevents null crashes)
        """
        if obj.user:
            return obj.user.email
        return None