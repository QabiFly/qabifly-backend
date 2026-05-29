from django.contrib import admin
from .models import Coupon, CouponUsage


class CouponUsageInline(admin.TabularInline):
    model = CouponUsage
    extra = 0
    readonly_fields = ("user", "order", "discount_applied", "used_at")
    can_delete = False


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display  = ("code", "discount_type", "discount_value", "shop",
                      "uses_count", "is_active", "valid_until")
    list_filter   = ("discount_type", "is_active")
    search_fields = ("code", "shop__name")
    readonly_fields = ("id", "uses_count", "created_at")
    inlines = [CouponUsageInline]