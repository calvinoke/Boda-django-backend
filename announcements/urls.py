from django.urls import path
from .views import (
    AnnouncementListView,
    AnnouncementCreateView,
    CondolenceListView
)

urlpatterns = [
    path('list/', AnnouncementListView.as_view()),
    path('create/', AnnouncementCreateView.as_view()),
    path('condolences/', CondolenceListView.as_view()),
]