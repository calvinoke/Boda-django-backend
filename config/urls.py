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
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),

    # Auth
    path('api/accounts/', include('accounts.urls')),

    # JWT
    path('api/token/', TokenObtainPairView.as_view()),
    path('api/token/refresh/', TokenRefreshView.as_view()),

    # Apps
    path('api/riders/', include('riders.urls')),
    path('api/contacts/', include('contacts.urls')),
    path('api/verification/', include('verification.urls')),
    path('api/location/', include('location.urls')),
    path('api/announcements/', include('announcements.urls')),
    path('api/adminpanel/', include('adminpanel.urls')),
]

from django.contrib import admin
from django.urls import path, include

urlpatterns = [

    path('admin/', admin.site.urls),

    path('api/v1/auth/', include('accounts.urls')),

    path('api/v1/', include('riders.urls')),

    path('api/v1/', include('contacts.urls')),

    path('api/v1/', include('verification.urls')),

    path(
    'api/v1/admin/',
    include('adminpanel.urls')
),
]