import json
from channels.generic.websocket import (
    AsyncWebsocketConsumer
)


# =========================================================
# ADMIN DASHBOARD CONSUMER
# =========================================================

class AdminDashboardConsumer(

    AsyncWebsocketConsumer
):

    async def connect(self):

        self.room_group_name = "admin_dashboard"

        await self.channel_layer.group_add(

            self.room_group_name,

            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):

        await self.channel_layer.group_discard(

            self.room_group_name,

            self.channel_name
        )

    async def send_admin_notification(

        self,
        event
    ):

        await self.send(

            text_data=json.dumps({

                "message": event["message"]
            })
        )