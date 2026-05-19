from math import radians, sin, cos, sqrt, atan2

from django.utils import timezone

from stages.models import Stage
from riders.models import RiderProfile, GuestRider

from .models import SuspiciousEvent

# =========================================================
# DISTANCE CALCULATION (HAVERSINE)
# =========================================================

def calculate_distance(lat1, lon1, lat2, lon2):

    """
    Calculate distance between two GPS points in meters
    """

    R = 6371  # Earth radius in KM

    dlat = radians(float(lat2) - float(lat1))
    dlon = radians(float(lon2) - float(lon1))

    a = (
        sin(dlat / 2) ** 2
        + cos(radians(float(lat1)))
        * cos(radians(float(lat2)))
        * sin(dlon / 2) ** 2
    )

    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c * 1000


# =========================================================
# CHECK IF RIDER LEFT STAGE AREA
# =========================================================

def is_out_of_stage(
    rider_lat,
    rider_lon,
    stage_lat,
    stage_lon,
    allowed_radius=300
):

    """
    Returns True if rider is outside allowed radius
    """

    distance = calculate_distance(
        rider_lat,
        rider_lon,
        stage_lat,
        stage_lon
    )

    return distance > allowed_radius


# =========================================================
# AUTO FINE GENERATOR
# =========================================================

def trigger_auto_fine(
    user,
    reason,
    amount,
    location
):

    from fines.models import Fine

    Fine.objects.create(

        issued_by=None,

        rider=(
            user.rider_profile
            if hasattr(user, 'rider_profile')
            else None
        ),

        guest_rider=(
            user.guest_rider_profile
            if hasattr(user, 'guest_rider_profile')
            else None
        ),

        reason=reason,

        amount=amount,

        status='pending',

        latitude=location.get('lat'),

        longitude=location.get('lng'),
    )


# =========================================================
# CHECK STAGE VIOLATION
# =========================================================

def check_stage_violation(
    rider=None,
    guest_rider=None,
    latitude=None,
    longitude=None
):

    """
    Detect if rider moved outside stage radius
    """

    profile = rider or guest_rider

    if not profile:
        return False

    stage = getattr(profile, 'stage', None)

    if not stage:
        return False

    if not stage.latitude or not stage.longitude:
        return False

    outside = is_out_of_stage(

        rider_lat=latitude,

        rider_lon=longitude,

        stage_lat=stage.latitude,

        stage_lon=stage.longitude,

        allowed_radius=500
    )

    if outside:

        SuspiciousEvent.objects.create(

            rider=rider,

            guest_rider=guest_rider,

            event_type='out_of_stage',

            description='Rider moved outside allowed stage zone',

            latitude=latitude,

            longitude=longitude,
        )

        user = (
            rider.user
            if rider
            else guest_rider.user
        )

        trigger_auto_fine(

            user=user,

            reason='Out of stage boundary',

            amount=20000,

            location={
                'lat': latitude,
                'lng': longitude
            }
        )

    return outside