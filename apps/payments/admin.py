from django.contrib import admin
from .models import Payment, PaymentSplit

class PaymentSplitInline(admin.TabularInline):
    model = PaymentSplit
    extra = 0
    readonly_fields = ("amount", "percent", "is_credited", "credited_at")

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display  = ("order", "method", "status", "amount", "utr_number", "verified_at")
    list_filter   = ("method", "status")
    search_fields = ("order__order_number", "utr_number")
    readonly_fields = ("id", "created_at", "upi_deep_link")
    inlines = [PaymentSplitInline]