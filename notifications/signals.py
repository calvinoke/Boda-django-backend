from django.db.models.signals import post_save
from django.dispatch import receiver

from riders.models import RiderProfile

from .tasks import create_notification

@receiver(post_save, sender=RiderProfile)
def rider_approval_notification(
    sender,
    instance,
    created,
    **kwargs
):

    if instance.status == 'approved':

        create_notification.delay(

            instance.user.id,

            "Verification Approved",

            "Your rider account has been approved.",

            "verification"
        )