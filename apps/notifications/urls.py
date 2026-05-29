from django.urls import path
from .views import (
    MyNotificationsView,
    UnreadCountView,
    MarkReadView,
    MarkAllReadView,
    AdminBroadcastView,
)

urlpatterns = [
    path("",                                MyNotificationsView.as_view(), name="notifications"),
    path("unread-count/",                   UnreadCountView.as_view(),     name="unread-count"),
    path("mark-all-read/",                  MarkAllReadView.as_view(),     name="mark-all-read"),
    path("<uuid:notif_id>/read/",           MarkReadView.as_view(),        name="notif-read"),
    path("admin/broadcast/",                AdminBroadcastView.as_view(),  name="admin-broadcast"),
]