from django.db.models.signals import (
    post_save
)
from django.dispatch import receiver
from .models import (
    RiderProfile,
    GuestRider
)
from .tasks import (

    refresh_riders_cache,

    refresh_guest_riders_cache
)


# =========================================================
# RIDER PROFILE SIGNAL
# =========================================================

@receiver(post_save, sender=RiderProfile)
def rider_saved_handler(

    sender,

    instance,

    created,

    **kwargs
):

    refresh_riders_cache.delay()


# =========================================================
# GUEST RIDER SIGNAL
# =========================================================

@receiver(post_save, sender=GuestRider)
def guest_rider_saved_handler(

    sender,

    instance,

    created,

    **kwargs
):

    refresh_guest_riders_cache.delay()