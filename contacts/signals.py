from django.db.models.signals import (post_save,post_delete)
from django.dispatch import receiver
from .models import EmergencyContact
from .tasks import (refresh_contact_cache,clear_contact_cache,cache_total_contacts)


# =========================================================
# SAVE SIGNAL
# =========================================================

@receiver(
    post_save,
    sender=EmergencyContact
)
def contact_saved(
    sender,
    instance,
    created,
    **kwargs
):

    user_id = instance.rider.user.id

    refresh_contact_cache.delay(
        user_id
    )

    cache_total_contacts.delay()


# =========================================================
# DELETE SIGNAL
# =========================================================

@receiver(
    post_delete,
    sender=EmergencyContact
)
def contact_deleted(
    sender,
    instance,
    **kwargs
):

    user_id = instance.rider.user.id

    clear_contact_cache.delay(
        user_id
    )

    cache_total_contacts.delay()