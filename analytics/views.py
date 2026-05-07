from rest_framework.views import APIView
from rest_framework.response import Response
from riders.models import RiderProfile
from verification.models import RiderVerification
from announcements.models import Announcement

class SystemStatsAPIView(APIView):

    def get(self, request):

        total_riders = RiderProfile.objects.count()

        approved_riders = RiderProfile.objects.filter(status='approved').count()

        pending_riders = RiderProfile.objects.filter(status='pending').count()

        suspended_riders = RiderProfile.objects.filter(status='suspended').count()

        verified_riders = RiderVerification.objects.filter(is_verified=True).count()

        return Response({

            "total_riders": total_riders,

            "approved_riders": approved_riders,

            "pending_riders": pending_riders,

            "suspended_riders": suspended_riders,

            "verified_riders": verified_riders,
        })