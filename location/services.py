import logging
from math import radians, sin, cos, sqrt, atan2
from django.utils import timezone
from stages.models import Stage
from riders.models import RiderProfile, GuestRider
from .models import SuspiciousEvent

logger = logging.getLogger("geo.tracking")


# =========================================================
# DISTANCE CALCULATION (HAVERSINE)
# =========================================================

def calculate_distance(lat1, lon1, lat2, lon2):

    try:
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

        distance = R * c * 1000

        logger.debug(
            f"Distance calculated | lat1={lat1}, lon1={lon1}, lat2={lat2}, lon2={lon2}, distance={distance}"
        )

        return distance

    except Exception as exc:
        logger.error(f"Distance calculation failed | error={str(exc)}")
        return 0


# =========================================================
# STAGE VIOLATION CHECK
# =========================================================

def is_out_of_stage(
    rider_lat,
    rider_lon,
    stage_lat,
    stage_lon,
    allowed_radius=300
):

    distance = calculate_distance(
        rider_lat,
        rider_lon,
        stage_lat,
        stage_lon
    )

    result = distance > allowed_radius

    logger.info(
        f"Stage check | distance={distance} | allowed={allowed_radius} | out_of_stage={result}"
    )

    return result


# =========================================================
# AUTO FINE GENERATOR
# =========================================================

def trigger_auto_fine(user, reason, amount, location):

    from fines.models import Fine

    try:
        fine = Fine.objects.create(
            issued_by=None,
            rider=getattr(user, "rider_profile", None),
            guest_rider=getattr(user, "guest_rider_profile", None),
            reason=reason,
            amount=amount,
            status="pending",
            latitude=location.get("lat"),
            longitude=location.get("lng"),
        )

        logger.warning(
            f"Auto fine triggered | fine_id={fine.id} | user_id={user.id} | reason={reason}"
        )

        return fine

    except Exception as exc:
        logger.error(
            f"Auto fine failed | user_id={getattr(user, 'id', None)} | error={str(exc)}"
        )
        return None


# =========================================================
# STAGE VIOLATION DETECTOR
# =========================================================

def check_stage_violation(
    rider=None,
    guest_rider=None,
    latitude=None,
    longitude=None
):

    try:

        profile = rider or guest_rider

        if not profile:
            logger.info("No profile provided for stage check")
            return False

        stage = getattr(profile, "stage", None)

        if not stage:
            logger.info(f"No stage assigned | user={profile.user.id}")
            return False

        if not stage.latitude or not stage.longitude:
            logger.warning(f"Stage missing coordinates | stage_id={stage.id}")
            return False

        outside = is_out_of_stage(
            rider_lat=latitude,
            rider_lon=longitude,
            stage_lat=stage.latitude,
            stage_lon=stage.longitude,
            allowed_radius=500
        )

        if outside:

            event = SuspiciousEvent.objects.create(
                rider=rider,
                guest_rider=guest_rider,
                event_type="out_of_stage",
                description="Rider moved outside allowed stage zone",
                latitude=latitude,
                longitude=longitude,
            )

            logger.warning(
                f"Suspicious event created | event_id={event.id}"
            )

            user = rider.user if rider else guest_rider.user

            trigger_auto_fine(
                user=user,
                reason="Out of stage boundary",
                amount=20000,
                location={"lat": latitude, "lng": longitude},
            )

        return outside

    except Exception as exc:
        logger.error(f"Stage violation check failed | error={str(exc)}")
        return False