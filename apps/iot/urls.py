from django.urls import path
from .views import (
    IngestSensorDataView,
    CurrentWeatherView,
    NodeListView,
    AdminCreateNodeView,
)

urlpatterns = [
    path("ingest/",              IngestSensorDataView.as_view(), name="iot-ingest"),
    path("weather/",             CurrentWeatherView.as_view(),   name="iot-weather"),
    path("nodes/",               NodeListView.as_view(),         name="iot-nodes"),
    path("admin/nodes/create/",  AdminCreateNodeView.as_view(),  name="iot-node-create"),
]