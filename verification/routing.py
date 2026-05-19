from django.urls import re_path
from .consumers import VerificationConsumer


websocket_urlpatterns = [

    re_path(
        r'ws/verification/$',
        VerificationConsumer.as_asgi()
    ),
]