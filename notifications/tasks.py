from celery import shared_task

from .models import Notification

@shared_task
def create_notification(

    user_id,

    title,

    message,

    notification_type='general'
):

    from accounts.models import User

    try:

        user = User.objects.get(id=user_id)

        Notification.objects.create(

            user=user,

            title=title,

            message=message,

            notification_type=notification_type
        )

        print(f"Notification sent to {user.email}")

    except User.DoesNotExist:

        print("User not found")