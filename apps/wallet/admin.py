from django.contrib import admin
from .models import Wallet, WalletTransaction, WithdrawalRequest


class WalletTransactionInline(admin.TabularInline):
    model  = WalletTransaction
    extra  = 0
    readonly_fields = ("id", "txn_type", "source", "amount", "balance_after",
                       "description", "reference", "created_at")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display  = ("user", "balance", "total_earned", "total_spent", "total_withdrawn")
    search_fields = ("user__email", "user__full_name")
    readonly_fields = ("id", "total_earned", "total_spent", "total_withdrawn",
                       "created_at", "updated_at")
    inlines = [WalletTransactionInline]


@admin.register(WithdrawalRequest)
class WithdrawalRequestAdmin(admin.ModelAdmin):
    list_display  = ("wallet", "amount", "upi_id", "status", "created_at")
    list_filter   = ("status",)
    readonly_fields = ("id", "created_at")