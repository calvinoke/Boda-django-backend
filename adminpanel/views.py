from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from riders.models import RiderProfile

from accounts.permissions import IsAdminRole

class ApproveRiderAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdminRole
    ]

    def post(self, request, rider_id):

        try:

            rider = RiderProfile.objects.get(id=rider_id)

            rider.status = 'approved'

            rider.save()

            return Response({
                'message': 'Rider approved successfully'
            })

        except RiderProfile.DoesNotExist:

            return Response({
                'error': 'Rider not found'
            }, status=404)


class SuspendRiderAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdminRole
    ]

    def post(self, request, rider_id):

        try:

            rider = RiderProfile.objects.get(id=rider_id)

            rider.status = 'suspended'

            rider.save()

            return Response({
                'message': 'Rider suspended successfully'
            })

        except RiderProfile.DoesNotExist:

            return Response({
                'error': 'Rider not found'
            }, status=404)