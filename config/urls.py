from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [

    # =====================================================
    # ADMIN
    # =====================================================
    path('admin/', admin.site.urls),

    # =====================================================
    # CORE APPS (ALL 12 INCLUDED)
    # =====================================================
    path('api/accounts/', include('accounts.urls')),
    path('api/riders/', include('riders.urls')),
    path('api/contacts/', include('contacts.urls')),  # ✅ FIXED (MISSING BEFORE)
    path('api/location/', include('location.urls')),
    path('api/verification/', include('verification.urls')),
    path('api/announcements/', include('announcements.urls')),
    path('api/notifications/', include('notifications.urls')),
    path('api/stages/', include('stages.urls')),
    path('api/fines/', include('fines.urls')),
    path('api/security/', include('security.urls')),

    # =====================================================
    # SYSTEM MODULES
    # =====================================================
    path('api/analytics/', include('analytics.urls')),
    path('api/adminpanel/', include('adminpanel.urls')),
]

# =========================================================
# MEDIA FILES
# =========================================================
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )