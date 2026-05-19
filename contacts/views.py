from rest_framework import viewsets
from rest_framework.permissions import (IsAuthenticated)
from django.core.cache import cache
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import EmergencyContact
from .serializers import (EmergencyContactSerializer)
from .tasks import (refresh_contact_cache)


class EmergencyContactViewSet(
    viewsets.ModelViewSet
):

    serializer_class = (
        EmergencyContactSerializer
    )

    permission_classes = [
        IsAuthenticated
    ]

    search_fields = [

        'name',

        'phone_number',

        'relationship'
    ]

    ordering_fields = [
        'created_at'
    ]

    # =====================================================
    # QUERYSET
    # =====================================================

    def get_queryset(self):

        user = self.request.user

        return EmergencyContact.objects.select_related(
            'rider',
            'rider__user'
        ).filter(
            rider__user=user
        )

    # =====================================================
    # CREATE
    # =====================================================

    def perform_create(
        self,
        serializer
    ):

        contact = serializer.save(

            rider=self.request.user.rider_profile
        )

        refresh_contact_cache.delay(
            self.request.user.id
        )

    # =====================================================
    # UPDATE
    # =====================================================

    def perform_update(
        self,
        serializer
    ):

        serializer.save()

        refresh_contact_cache.delay(
            self.request.user.id
        )

    # =====================================================
    # DELETE
    # =====================================================

    def perform_destroy(
        self,
        instance
    ):

        instance.delete()

        refresh_contact_cache.delay(
            self.request.user.id
        )

    # =====================================================
    # REDIS CACHE VIEW
    # =====================================================

    @action(
        detail=False,
        methods=['get']
    )
    def cached_contacts(
        self,
        request
    ):

        cache_key = (
            f"rider_contacts_{request.user.id}"
        )

        data = cache.get(cache_key)

        return Response({

            "cached": True,

            "data": data or []
        })