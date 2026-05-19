from django.urls import re_path
from .consumers import (

    AnalyticsDashboardConsumer,

    SystemStatsConsumer
)

websocket_urlpatterns = [

    re_path(
        r'ws/analytics/dashboard/$',
        AnalyticsDashboardConsumer.as_asgi()
    ),

    re_path(
        r'ws/analytics/stats/$',
        SystemStatsConsumer.as_asgi()
    ),
]