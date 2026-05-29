from django.contrib import admin
from .models import Product, ProductCategory, ProductImage, ProductVariant, ProductReview


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "parent", "is_active", "sort_order")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display  = ("name", "shop", "category", "price", "stock", "status", "is_featured")
    list_filter   = ("status", "is_featured", "category")
    search_fields = ("name", "shop__name")
    readonly_fields = ("id", "total_sold", "average_rating", "total_reviews", "created_at")


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ("product", "user", "rating", "is_visible", "created_at")
    list_filter  = ("rating", "is_visible")