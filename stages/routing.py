from django.urls import re_path
from .consumers import StageConsumer


websocket_urlpatterns = [

    re_path(
        r'ws/stages/$',
        StageConsumer.as_asgi()
    ),
]