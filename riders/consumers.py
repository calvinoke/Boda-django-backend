import json

from channels.generic.websocket import (
    AsyncWebsocketConsumer
)


class RiderConsumer(
    AsyncWebsocketConsumer
):

    async def connect(self):

        self.room_group_name = "riders"

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

    # =====================================================
    # SEND LIVE RIDER STATUS
    # =====================================================

    async def send_rider_status(
        self,
        event
    ):

        await self.send(
            text_data=json.dumps(
                event["data"]
            )
        )