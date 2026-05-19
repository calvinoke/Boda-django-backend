import json
from channels.generic.websocket import AsyncWebsocketConsumer


class NotificationConsumer(
    AsyncWebsocketConsumer
):

    async def connect(self):

        self.user = self.scope["user"]

        # =============================================
        # AUTH CHECK
        # =============================================

        if self.user.is_anonymous:

            await self.close()

            return

        self.room_group_name = (
            f"notifications_{self.user.id}"
        )

        # =============================================
        # JOIN GROUP
        # =============================================

        await self.channel_layer.group_add(

            self.room_group_name,

            self.channel_name
        )

        await self.accept()

    async def disconnect(
        self,
        close_code
    ):

        await self.channel_layer.group_discard(

            self.room_group_name,

            self.channel_name
        )

    # =============================================
    # SEND REALTIME NOTIFICATION
    # =============================================

    async def send_notification(
        self,
        event
    ):

        await self.send(
            text_data=json.dumps(
                event["data"]
            )
        )