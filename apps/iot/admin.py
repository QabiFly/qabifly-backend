from django.contrib import admin
from .models import IoTNode


@admin.register(IoTNode)
class IoTNodeAdmin(admin.ModelAdmin):
    list_display  = ("node_id", "name", "location", "status", "last_seen_at")
    list_filter   = ("status",)
    search_fields = ("node_id", "name")
    readonly_fields = ("id", "created_at", "last_seen_at")