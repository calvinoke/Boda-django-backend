from django.urls import re_path
from .consumers import RiderConsumer

websocket_urlpatterns = [

    re_path(
        r'ws/riders/$',
        RiderConsumer.as_asgi()
    ),
]