"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_asgi_application()
import os

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

from django.core.asgi import get_asgi_application

import location.routing

os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE',
    'config.settings'
)

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({

    'http': django_asgi_app,

    'websocket': AuthMiddlewareStack(

        URLRouter(

            location.routing.websocket_urlpatterns
        )
    ),
})