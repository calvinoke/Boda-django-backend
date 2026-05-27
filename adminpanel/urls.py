from django.urls import path
from .views import (ApproveRiderAPIView,SuspendRiderAPIView)

urlpatterns = [

    path('approve-rider/<int:rider_id>/',ApproveRiderAPIView.as_view(),name='approve-rider'),

    path('suspend-rider/<int:rider_id>/',SuspendRiderAPIView.as_view(),name='suspend-rider'),
]