from django.core.cache import cache
from rest_framework import viewsets
from rest_framework.permissions import (
    IsAuthenticated
)
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Notification
from .serializers import (
    NotificationSerializer
)
from .tasks import (
    refresh_notifications_cache
)


class NotificationViewSet(viewsets.ModelViewSet):

    serializer_class = (
        NotificationSerializer
    )

    permission_classes = [
        IsAuthenticated
    ]

    # =====================================================
    # GET QUERYSET
    # =====================================================

    def get_queryset(self):

        user = self.request.user

        # =============================================
        # ADMINS SEE ALL
        # =============================================

        if hasattr(user, 'role') and user.role in [

            'super_admin',

            'stage_chairman',

            'stage_secretary',

            'stage_defense'
        ]:

            return Notification.objects.all()

        # =============================================
        # NORMAL USERS SEE OWN
        # =============================================

        return Notification.objects.filter(
            user=user
        )

    # =====================================================
    # MARK AS READ
    # =====================================================

    @action(
        detail=True,
        methods=['post']
    )
    def mark_as_read(
        self,
        request,
        pk=None
    ):

        notification = self.get_object()

        notification.is_read = True

        notification.save()

        refresh_notifications_cache.delay(
            request.user.id
        )

        return Response({

            "message":
            "Notification marked as read"
        })

    # =====================================================
    # GET CACHED NOTIFICATIONS
    # =====================================================

    @action(
        detail=False,
        methods=['get']
    )
    def cached(self, request):

        cache_key = (
            f"user_notifications_{request.user.id}"
        )

        data = cache.get(cache_key)

        if not data:

            refresh_notifications_cache.delay(
                request.user.id
            )

            return Response({

                "message":
                "Cache rebuilding"
            })

        return Response(data)