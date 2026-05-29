from django.urls import path
from .views import (
    webhook,
    AdminWhatsAppStatsView,
    AdminSendBroadcastView,
)

urlpatterns = [
    path("webhook/",          webhook,                     name="whatsapp-webhook"),
    path("admin/stats/",      AdminWhatsAppStatsView.as_view(), name="whatsapp-stats"),
    path("admin/broadcast/",  AdminSendBroadcastView.as_view(), name="whatsapp-broadcast"),
]
