
from rest_framework import viewsets
from rest_framework.permissions import (IsAuthenticated)
from .models import (Announcement,Condolence)
from .serializers import (AnnouncementSerializer,CondolenceSerializer)


class AnnouncementViewSet(
    viewsets.ModelViewSet
):

    serializer_class = (
        AnnouncementSerializer
    )

    permission_classes = [
        IsAuthenticated
    ]

    queryset = Announcement.objects.select_related(
        'created_by'
    )

    def perform_create(
        self,
        serializer
    ):

        serializer.save(
            created_by=self.request.user
        )


class CondolenceViewSet(
    viewsets.ModelViewSet
):

    serializer_class = (
        CondolenceSerializer
    )

    permission_classes = [
        IsAuthenticated
    ]

    queryset = Condolence.objects.select_related(

        'rider',

        'reported_by',

        'verified_by'
    )

    def perform_create(
        self,
        serializer
    ):

        serializer.save(
            reported_by=self.request.user
        )