from django.urls import path
from .views import LocationCreateView, LocationListView

urlpatterns = [
    path('create/', LocationCreateView.as_view()),
    path('list/', LocationListView.as_view()),
]