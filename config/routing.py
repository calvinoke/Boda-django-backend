"""
ASGI config for config project.
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

import location.routing

# =========================================================
# DJANGO SETTINGS
# =========================================================

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# =========================================================
# HTTP HANDLER
# =========================================================

django_asgi_app = get_asgi_application()

# =========================================================
# APPLICATION ROUTER
# =========================================================

application = ProtocolTypeRouter({

    "http": django_asgi_app,

    "websocket": AuthMiddlewareStack(
        URLRouter(
            location.routing.websocket_urlpatterns
        )
    ),
})