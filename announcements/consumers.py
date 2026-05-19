import json
from channels.generic.websocket import (
    AsyncWebsocketConsumer
)


# =========================================================
# ANNOUNCEMENT CONSUMER
# =========================================================

class AnnouncementConsumer(
    AsyncWebsocketConsumer
):

    async def connect(self):

        self.room_group_name = "announcements"

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

    async def send_announcement(
        self,
        event
    ):

        await self.send(
            text_data=json.dumps(
                event["message"]
            )
        )


# =========================================================
# CONDOLENCE CONSUMER
# =========================================================

class CondolenceConsumer(
    AsyncWebsocketConsumer
):

    async def connect(self):

        self.room_group_name = "condolences"

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

    async def send_condolence(
        self,
        event
    ):

        await self.send(
            text_data=json.dumps(
                event["message"]
            )
        )