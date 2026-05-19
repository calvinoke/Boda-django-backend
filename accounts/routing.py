from django.urls import re_path
from .consumers import (
    AccountsConsumer
)

websocket_urlpatterns = [

    re_path(

        r'ws/accounts/$',

        AccountsConsumer.as_asgi()
    ),
]