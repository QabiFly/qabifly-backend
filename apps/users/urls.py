from django.urls import path
from .views import MeView, UpdateProfileView, DeleteAccountView

urlpatterns = [
    path("me/", MeView.as_view(), name="user-me"),
    path("me/update/", UpdateProfileView.as_view(), name="user-update"),
    path("me/delete/", DeleteAccountView.as_view(), name="user-delete"),
]