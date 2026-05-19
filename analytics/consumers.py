import json
from channels.generic.websocket import (
    AsyncWebsocketConsumer
)


# =========================================================
# ADMIN DASHBOARD CONSUMER
# =========================================================

class AnalyticsDashboardConsumer(
    AsyncWebsocketConsumer
):

    async def connect(self):

        self.room_group_name = (
            "admin_dashboard"
        )

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

    async def send_admin_update(
        self,
        event
    ):

        await self.send(
            text_data=json.dumps(
                event["message"]
            )
        )


# =========================================================
# SYSTEM STATS CONSUMER
# =========================================================

class SystemStatsConsumer(
    AsyncWebsocketConsumer
):

    async def connect(self):

        self.room_group_name = (
            "admin_stats"
        )

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

    async def send_stats_update(
        self,
        event
    ):

        await self.send(
            text_data=json.dumps(
                event["message"]
            )
        )