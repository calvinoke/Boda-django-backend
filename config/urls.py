"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""


from django.contrib import admin
from django.urls import path, include

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [

    path('admin/', admin.site.urls),

    # =====================================================
    # API ROUTES
    # =====================================================

    path('api/accounts/', include('accounts.urls')),

    path('api/riders/', include('riders.urls')),

    path('api/location/', include('location.urls')),

    path('api/verification/', include('verification.urls')),

    path('api/announcements/', include('announcements.urls')),

    path('api/notifications/', include('notifications.urls')),
    # STAGES APP (NEW)
    path('api/stages', include('stages.urls')),
    path('api/fines/', include('fines.urls')),
    path('api/location/', include('location.urls')),
    path('api/tracking/', include('tracking.urls')),
]

# MEDIA FILES
if settings.DEBUG:

    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )