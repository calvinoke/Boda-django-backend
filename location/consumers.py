import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from .tasks import (save_location_task, trigger_auto_fine_task, create_suspicious_event_task)

logger = logging.getLogger(__name__)


class RiderLocationConsumer( AsyncWebsocketConsumer):

    # =========================================================
    # CONNECT
    # =========================================================

    async def connect(self):

        self.room_group_name = "live_tracking"

        # JOIN REDIS CHANNEL GROUP
        await self.channel_layer.group_add(

            self.room_group_name,

            self.channel_name
        )

        await self.accept()

        logger.info(
            f"WebSocket connected: {self.channel_name}"
        )

    # =========================================================
    # DISCONNECT
    # =========================================================

    async def disconnect(self, close_code):

        await self.channel_layer.group_discard(

            self.room_group_name,

            self.channel_name
        )

        logger.info(
            f"WebSocket disconnected: {self.channel_name}"
        )

    # =========================================================
    # RECEIVE LOCATION
    # =========================================================

    async def receive(self, text_data):

        try:

            data = json.loads(text_data)

            user_id = data.get("user_id")

            latitude = data.get("latitude")

            longitude = data.get("longitude")

            speed = float(data.get("speed", 0))

            heading = data.get("heading")

            # =================================================
            # VALIDATION
            # =================================================

            if not user_id:

                await self.send(json.dumps({
                    "error": "user_id is required"
                }))

                return

            if latitude is None or longitude is None:

                await self.send(json.dumps({
                    "error": "latitude and longitude required"
                }))

                return

            # =================================================
            # SAVE LOCATION USING CELERY
            # =================================================

            save_location_task.delay(

                user_id=user_id,

                latitude=latitude,

                longitude=longitude,

                speed=speed,

                heading=heading
            )

            # =================================================
            # SPEED VIOLATION DETECTION
            # =================================================

            if speed > 120:

                # CREATE SECURITY EVENT
                create_suspicious_event_task.delay(

                    user_id=user_id,

                    event_type='speed_violation',

                    description='Overspeeding detected',

                    latitude=latitude,

                    longitude=longitude
                )

                # AUTO FINE
                trigger_auto_fine_task.delay(

                    user_id=user_id,

                    reason='Overspeeding',

                    amount=50000,

                    latitude=latitude,

                    longitude=longitude
                )

            # =================================================
            # BROADCAST LIVE LOCATION USING REDIS
            # =================================================

            await self.channel_layer.group_send(

                self.room_group_name,

                {

                    "type": "send_live_location",

                    "user_id": user_id,

                    "latitude": latitude,

                    "longitude": longitude,

                    "speed": speed,

                    "heading": heading,
                }
            )

        except Exception as e:

            logger.error(str(e))

            await self.send(text_data=json.dumps({

                "error": "Something went wrong",

                "details": str(e)
            }))

    # =========================================================
    # SEND LOCATION TO ALL CLIENTS
    # =========================================================

    async def send_live_location(
        self,
        event
    ):

        await self.send(

            text_data=json.dumps({

                "type": "live_location",

                "user_id": event["user_id"],

                "latitude": event["latitude"],

                "longitude": event["longitude"],

                "speed": event["speed"],

                "heading": event["heading"],
            })
        )