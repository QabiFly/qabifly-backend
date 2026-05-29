from django.contrib import admin
from .models import Landmark, DeliveryZone


@admin.register(Landmark)
class LandmarkAdmin(admin.ModelAdmin):
    list_display  = ("name", "landmark_type", "village", "is_active", "created_at")
    list_filter   = ("landmark_type", "is_active", "village")
    search_fields = ("name", "village")


@admin.register(DeliveryZone)
class DeliveryZoneAdmin(admin.ModelAdmin):
    list_display = ("name", "radius_km", "is_active", "created_at")
    list_filter  = ("is_active",)