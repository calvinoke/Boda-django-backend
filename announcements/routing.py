from django.urls import re_path
from .consumers import ( AnnouncementConsumer,CondolenceConsumer)

websocket_urlpatterns = [

    re_path( r'ws/announcements/$',AnnouncementConsumer.as_asgi()),

    re_path( r'ws/condolences/$', CondolenceConsumer.as_asgi()),
]