from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Announcement, Condolence
from .serializers import (
    AnnouncementSerializer,
    CondolenceSerializer
)

from accounts.permissions import IsAdminRole

class AnnouncementViewSet(viewsets.ModelViewSet):

    serializer_class = AnnouncementSerializer

    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        queryset = Announcement.objects.select_related(
            'created_by'
        ).all()

        announcement_type = self.request.query_params.get('type')

        if announcement_type:

            queryset = queryset.filter(
                announcement_type=announcement_type
            )

        return queryset

    def perform_create(self, serializer):

        serializer.save(
            created_by=self.request.user
        )


class CondolenceViewSet(viewsets.ModelViewSet):

    serializer_class = CondolenceSerializer

    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        return Condolence.objects.select_related(
            'rider',
            'reported_by',
            'verified_by'
        ).all()

    def perform_create(self, serializer):

        serializer.save(
            reported_by=self.request.user
        )