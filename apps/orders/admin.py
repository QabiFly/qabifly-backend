from django.contrib import admin
from .models import Order, OrderItem, OrderStatusLog

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("line_total",)

class OrderStatusLogInline(admin.TabularInline):
    model = OrderStatusLog
    extra = 0
    readonly_fields = ("from_status", "to_status", "changed_by", "changed_at")

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display  = ("order_number", "buyer", "shop", "status", "payment_method", "total_amount", "created_at")
    list_filter   = ("status", "payment_method", "payment_status")
    search_fields = ("order_number", "buyer__email", "shop__name")
    readonly_fields = ("id", "order_number", "created_at", "updated_at")
    inlines = [OrderItemInline, OrderStatusLogInline]