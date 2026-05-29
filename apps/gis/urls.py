from django.urls import path
from .views import (
    LandmarkListView,
    AdminCreateLandmarkView,
    DeliveryZoneListView,
    CheckPointInZoneView,
    AdminCreateZoneView,
)

urlpatterns = [
    path("landmarks/",           LandmarkListView.as_view(),      name="landmarks"),
    path("zones/",               DeliveryZoneListView.as_view(),  name="zones"),
    path("zones/check/",         CheckPointInZoneView.as_view(),  name="zone-check"),
    path("admin/landmarks/",     AdminCreateLandmarkView.as_view(), name="admin-landmark"),
    path("admin/zones/",         AdminCreateZoneView.as_view(),   name="admin-zone"),
]