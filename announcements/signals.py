from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import ( Announcement,Condolence)
from .tasks import (broadcast_announcement_task,broadcast_condolence_task,refresh_announcements_cache)


# =========================================================
# ANNOUNCEMENT CREATED
# =========================================================

@receiver(
    post_save,
    sender=Announcement
)
def announcement_created_handler(
    sender,
    instance,
    created,
    **kwargs
):

    if created:

        broadcast_announcement_task.delay(
            instance.id
        )

        refresh_announcements_cache.delay()


# =========================================================
# CONDOLENCE CREATED
# =========================================================

@receiver(
    post_save,
    sender=Condolence
)
def condolence_created_handler(
    sender,
    instance,
    created,
    **kwargs
):

    if created:

        broadcast_condolence_task.delay(
            instance.id
        )

        refresh_announcements_cache.delay()