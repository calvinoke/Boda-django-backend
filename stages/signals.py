from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Stage
from .tasks import (

    broadcast_stage_update,

    refresh_stage_cache
)


# =========================================================
# STAGE CREATED / UPDATED
# =========================================================

@receiver(post_save, sender=Stage)
def stage_saved_handler(
    sender,
    instance,
    created,
    **kwargs
):

    if created:

        message = {

            "event": "stage_created",

            "stage_id": instance.id,

            "name": instance.name,

            "district": instance.district,

            "division": instance.division,
        }

    else:

        message = {

            "event": "stage_updated",

            "stage_id": instance.id,

            "name": instance.name,

            "district": instance.district,

            "division": instance.division,
        }

    # =====================================================
    # CELERY TASKS
    # =====================================================

    broadcast_stage_update.delay(message)

    refresh_stage_cache.delay()