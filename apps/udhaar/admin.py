from django.contrib import admin
from .models import UdhaarRecord, UdhaarPayment, SundayCollection


class UdhaarPaymentInline(admin.TabularInline):
    model = UdhaarPayment
    extra = 0
    readonly_fields = ("paid_at", "collected_by")


@admin.register(UdhaarRecord)
class UdhaarRecordAdmin(admin.ModelAdmin):
    list_display  = ("buyer", "shop", "amount", "amount_paid", "status", "due_date", "is_settled")
    list_filter   = ("status", "is_settled")
    search_fields = ("buyer__full_name", "buyer__phone", "shop__name")
    readonly_fields = ("id", "created_at", "settled_at")
    inlines = [UdhaarPaymentInline]


@admin.register(SundayCollection)
class SundayCollectionAdmin(admin.ModelAdmin):
    list_display = ("shop", "delivery_boy", "collection_date", "status", "total_collected")
    list_filter  = ("status",)