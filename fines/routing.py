from django.urls import re_path
from .consumers import FineConsumer


websocket_urlpatterns = [
    re_path(
        r"^ws/fines/$",
        FineConsumer.as_asgi(),
    ),
]