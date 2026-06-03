import logging
from celery import shared_task
from riders.models import RiderProfile, GuestRider
from .models import RiderLocation, SuspiciousEvent
from .services import check_stage_violation, trigger_auto_fine

logger = logging.getLogger("gps.tasks")


# =========================================================
# SAVE LOCATION TASK
# =========================================================

@shared_task
def save_location_task(user_id, latitude, longitude, speed=0, heading=None):

    try:

        # =====================================================
        # VALIDATION GUARDS
        # =====================================================

        if latitude is None or longitude is None:
            logger.warning(f"Invalid GPS data | user_id={user_id}")
            return None

        # =====================================================
        # FETCH USER TYPE
        # =====================================================

        rider = RiderProfile.objects.filter(user_id=user_id).first()
        guest_rider = GuestRider.objects.filter(user_id=user_id).first()

        if not rider and not guest_rider:
            logger.warning(f"No rider found | user_id={user_id}")
            return None

        # =====================================================
        # SAVE LOCATION
        # =====================================================

        location = RiderLocation.objects.create(
            rider=rider,
            guest_rider=guest_rider,
            latitude=latitude,
            longitude=longitude,
            speed=speed,
            heading=heading,
        )

        logger.info(
            f"Location saved | location_id={location.id} | user_id={user_id}"
        )

        # =====================================================
        # CHECK STAGE VIOLATION
        # =====================================================

        try:
            violation = check_stage_violation(
                rider=rider,
                guest_rider=guest_rider,
                latitude=latitude,
                longitude=longitude
            )

            logger.info(
                f"Stage check completed | user_id={user_id} | violation={violation}"
            )

        except Exception as exc:
            logger.error(
                f"Stage check failed | user_id={user_id} | error={str(exc)}"
            )

        return location.id

    except Exception as exc:

        logger.error(
            f"save_location_task failed | user_id={user_id} | error={str(exc)}"
        )
        return None


# =========================================================
# CREATE SUSPICIOUS EVENT TASK
# =========================================================

@shared_task
def create_suspicious_event_task(user_id, event_type, description, latitude, longitude):

    try:

        rider = RiderProfile.objects.filter(user_id=user_id).first()
        guest_rider = GuestRider.objects.filter(user_id=user_id).first()

        event = SuspiciousEvent.objects.create(
            rider=rider,
            guest_rider=guest_rider,
            event_type=event_type,
            description=description,
            latitude=latitude,
            longitude=longitude,
        )

        logger.warning(
            f"Suspicious event created | event_id={event.id} | user_id={user_id} | type={event_type}"
        )

        return event.id

    except Exception as exc:

        logger.error(
            f"suspicious event task failed | user_id={user_id} | error={str(exc)}"
        )
        return None


# =========================================================
# AUTO FINE TASK
# =========================================================

@shared_task
def trigger_auto_fine_task(user_id, reason, amount, latitude, longitude):

    try:

        rider = RiderProfile.objects.filter(user_id=user_id).first()
        guest_rider = GuestRider.objects.filter(user_id=user_id).first()

        user = None

        if rider:
            user = rider.user
        elif guest_rider:
            user = guest_rider.user

        if not user:
            logger.warning(f"No user for auto fine | user_id={user_id}")
            return None

        fine = trigger_auto_fine(
            user=user,
            reason=reason,
            amount=amount,
            location={
                "lat": latitude,
                "lng": longitude
            }
        )

        logger.warning(
            f"Auto fine triggered | user_id={user_id} | reason={reason} | amount={amount}"
        )

        return True

    except Exception as exc:

        logger.error(
            f"auto fine task failed | user_id={user_id} | error={str(exc)}"
        )
        return None