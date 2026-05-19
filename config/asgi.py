import os
from django.core.asgi import get_asgi_application
from channels.routing import (
    ProtocolTypeRouter,
    URLRouter,
)
from channels.auth import (
    AuthMiddlewareStack,
)

# =========================================================
# DJANGO SETTINGS
# =========================================================

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings"
)

django_asgi_app = get_asgi_application()

# =========================================================
# IMPORT WEBSOCKET ROUTING MODULES
# =========================================================

import accounts.routing
import notifications.routing
import riders.routing
import location.routing
import contacts.routing
import announcements.routing
import fines.routing
import analytics.routing
import adminpanel.routing
import stages.routing
import verification.routing
import security.routing

# =========================================================
# MAIN ASGI APPLICATION
# =========================================================

application = ProtocolTypeRouter({

    # =====================================================
    # NORMAL HTTP REQUESTS
    # =====================================================

    "http": django_asgi_app,

    # =====================================================
    # WEBSOCKET REQUESTS
    # =====================================================

    "websocket": AuthMiddlewareStack(

        URLRouter(

            # =================================================
            # ACCOUNTS
            # =================================================

            accounts.routing.websocket_urlpatterns +

            # =================================================
            # NOTIFICATIONS
            # =================================================

            notifications.routing.websocket_urlpatterns +

            # =================================================
            # RIDERS
            # =================================================

            riders.routing.websocket_urlpatterns +

            # =================================================
            # LOCATION TRACKING
            # =================================================

            location.routing.websocket_urlpatterns +

            # =================================================
            # EMERGENCY CONTACTS
            # =================================================

            contacts.routing.websocket_urlpatterns +

            # =================================================
            # ANNOUNCEMENTS
            # =================================================

            announcements.routing.websocket_urlpatterns +

            # =================================================
            # FINES
            # =================================================

            fines.routing.websocket_urlpatterns +

            # =================================================
            # ANALYTICS
            # =================================================

            analytics.routing.websocket_urlpatterns +

            # =================================================
            # ADMIN PANEL
            # =================================================

            adminpanel.routing.websocket_urlpatterns +

            # =================================================
            # STAGES
            # =================================================

            stages.routing.websocket_urlpatterns +

            # =================================================
            # VERIFICATION
            # =================================================

            verification.routing.websocket_urlpatterns +

            # =================================================
            # SECURITY ALERTS
            # =================================================

            security.routing.websocket_urlpatterns
        )
    ),
})