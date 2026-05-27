from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import (IsAuthenticated)
from riders.models import RiderProfile
from accounts.permissions import (IsAdminRole)
from .models import (RiderActivity,SystemLog)
from .tasks import (broadcast_admin_event,refresh_admin_cache)


# =========================================================
# APPROVE RIDER
# =========================================================

class ApproveRiderAPIView(APIView):

    permission_classes = [IsAuthenticated, IsAdminRole]

    def post(self,request,rider_id):

        try:

            rider = RiderProfile.objects.get(id=rider_id)

            rider.status = 'approved'

            rider.save()

            # =============================================
            # ACTIVITY LOG
            # =============================================

            RiderActivity.objects.create(

                rider=rider,

                action='approved',

                description='Rider approved'
            )

            # =============================================
            # SYSTEM LOG
            # =============================================

            SystemLog.objects.create(

                level='info',

                message=f'Rider {rider.user.email} approved'
            )

            # =============================================
            # CELERY + REDIS + WEBSOCKET
            # =============================================

            broadcast_admin_event.delay(

                f'Rider {rider.user.email} approved'
            )

            refresh_admin_cache.delay()

            return Response({

                'message':
                'Rider approved successfully'
            })

        except RiderProfile.DoesNotExist:

            return Response({

                'error': 'Rider not found'

            }, status=404)


# =========================================================
# SUSPEND RIDER
# =========================================================

class SuspendRiderAPIView(APIView):

    permission_classes = [

        IsAuthenticated,

        IsAdminRole
    ]

    def post(

        self,

        request,

        rider_id
    ):

        try:

            rider = RiderProfile.objects.get(
                id=rider_id
            )

            rider.status = 'suspended'

            rider.save()

            # =============================================
            # ACTIVITY LOG
            # =============================================

            RiderActivity.objects.create(

                rider=rider,

                action='suspended',

                description='Rider suspended'
            )

            # =============================================
            # SYSTEM LOG
            # =============================================

            SystemLog.objects.create(

                level='warning',

                message=f'Rider {rider.user.email} suspended'
            )

            # =============================================
            # CELERY + REDIS + WEBSOCKET
            # =============================================

            broadcast_admin_event.delay(

                f'Rider {rider.user.email} suspended'
            )

            refresh_admin_cache.delay()

            return Response({

                'message':
                'Rider suspended successfully'
            })

        except RiderProfile.DoesNotExist:

            return Response({

                'error': 'Rider not found'

            }, status=404)