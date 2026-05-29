from django.urls import path
from .views import (
    VideoCategoryListView,
    VideoListView,
    AdminCreateVideoView,
    AdminVideoListView,
    AdminToggleVideoView,
)

urlpatterns = [
    path("categories/",               VideoCategoryListView.as_view(), name="video-categories"),
    path("",                          VideoListView.as_view(),         name="video-list"),
    path("admin/create/",             AdminCreateVideoView.as_view(),  name="admin-video-create"),
    path("admin/list/",               AdminVideoListView.as_view(),    name="admin-video-list"),
    path("admin/<uuid:video_id>/toggle/", AdminToggleVideoView.as_view(), name="admin-video-toggle"),
]