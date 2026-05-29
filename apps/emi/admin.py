from django.contrib import admin
from .models import EMIPlan, EMIInstallment


class EMIInstallmentInline(admin.TabularInline):
    model = EMIInstallment
    extra = 0
    readonly_fields = ("paid_at",)


@admin.register(EMIPlan)
class EMIPlanAdmin(admin.ModelAdmin):
    list_display  = ("buyer", "order", "total_amount", "monthly_amount",
                      "months", "status", "start_date")
    list_filter   = ("status",)
    search_fields = ("buyer__email", "buyer__full_name", "order__order_number")
    readonly_fields = ("id", "created_at", "amount_paid")
    inlines = [EMIInstallmentInline]