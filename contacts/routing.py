from django.urls import re_path
from .consumers import EmergencyContactConsumer


websocket_urlpatterns = [

    re_path(
        r'ws/contacts/$',
        EmergencyContactConsumer.as_asgi()
    ),
]