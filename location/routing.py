from django.urls import re_path

from .consumers import RiderLocationConsumer

websocket_urlpatterns = [

    re_path(
        r"ws/location/$",
        RiderLocationConsumer.as_asgi()
    ),
]