from django.contrib import admin
from .models import Shop, ShopCategory, ShopDocument


@admin.register(ShopCategory)
class ShopCategoryAdmin(admin.ModelAdmin):
    list_display  = ("name", "slug", "is_active", "sort_order")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display   = ("name", "owner", "category", "status", "is_open", "average_rating", "created_at")
    list_filter    = ("status", "is_open", "category")
    search_fields  = ("name", "owner__email", "owner__full_name")
    readonly_fields = ("id", "created_at", "updated_at", "approved_at", "total_orders", "total_earnings")


@admin.register(ShopDocument)
class ShopDocumentAdmin(admin.ModelAdmin):
    list_display = ("shop", "doc_type", "is_verified", "uploaded_at")
    list_filter  = ("doc_type", "is_verified")