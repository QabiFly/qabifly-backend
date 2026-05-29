from django.contrib import admin
from .models import DeliveryBoyProfile, DeliveryAssignment, LocationLog, DeliveryRating


@admin.register(DeliveryBoyProfile)
class DeliveryBoyProfileAdmin(admin.ModelAdmin):
    list_display  = ("user", "availability", "vehicle_type", "total_deliveries",
                      "average_rating", "is_verified")
    list_filter   = ("availability", "vehicle_type", "is_verified")
    search_fields = ("user__email", "user__full_name")
    readonly_fields = ("id", "total_deliveries", "successful_deliveries",
                       "total_earned", "average_rating", "total_ratings")


@admin.register(DeliveryAssignment)
class DeliveryAssignmentAdmin(admin.ModelAdmin):
    list_display  = ("order", "delivery_boy", "status", "earning", "assigned_at")
    list_filter   = ("status", "assigned_by_admin")
    search_fields = ("order__order_number", "delivery_boy__email")
    readonly_fields = ("id", "assigned_at")


@admin.register(DeliveryRating)
class DeliveryRatingAdmin(admin.ModelAdmin):
    list_display = ("assignment", "rated_by", "rating", "created_at")
    list_filter  = ("rating",)