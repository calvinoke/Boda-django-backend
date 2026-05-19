from celery import shared_task

from riders.models import (
    RiderProfile,
    GuestRider
)

from .models import (
    RiderLocation,
    SuspiciousEvent
)

from .services import (
    check_stage_violation,
    trigger_auto_fine
)


# =========================================================
# SAVE LOCATION
# =========================================================

@shared_task
def save_location_task(
    user_id,
    latitude,
    longitude,
    speed=0,
    heading=None
):

    rider = RiderProfile.objects.filter(
        user_id=user_id
    ).first()

    guest_rider = GuestRider.objects.filter(
        user_id=user_id
    ).first()

    location = RiderLocation.objects.create(

        rider=rider,

        guest_rider=guest_rider,

        latitude=latitude,

        longitude=longitude,

        speed=speed,

        heading=heading,
    )

    # =====================================================
    # CHECK STAGE VIOLATIONS
    # =====================================================

    check_stage_violation(

        rider=rider,

        guest_rider=guest_rider,

        latitude=latitude,

        longitude=longitude
    )

    return location.id


# =========================================================
# CREATE SUSPICIOUS EVENT
# =========================================================

@shared_task
def create_suspicious_event_task(
    user_id,
    event_type,
    description,
    latitude,
    longitude
):

    rider = RiderProfile.objects.filter(
        user_id=user_id
    ).first()

    guest_rider = GuestRider.objects.filter(
        user_id=user_id
    ).first()

    SuspiciousEvent.objects.create(

        rider=rider,

        guest_rider=guest_rider,

        event_type=event_type,

        description=description,

        latitude=latitude,

        longitude=longitude,
    )


# =========================================================
# AUTO FINE TASK
# =========================================================

@shared_task
def trigger_auto_fine_task(
    user_id,
    reason,
    amount,
    latitude,
    longitude
):

    rider = RiderProfile.objects.filter(
        user_id=user_id
    ).first()

    guest_rider = GuestRider.objects.filter(
        user_id=user_id
    ).first()

    user = None

    if rider:
        user = rider.user

    elif guest_rider:
        user = guest_rider.user

    if user:

        trigger_auto_fine(

            user=user,

            reason=reason,

            amount=amount,

            location={
                'lat': latitude,
                'lng': longitude
            }
        )