from django.contrib import admin
from .models import Cart, CartItem

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ("line_total",)

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("user", "shop", "total_items", "subtotal", "updated_at")
    inlines = [CartItemInline]