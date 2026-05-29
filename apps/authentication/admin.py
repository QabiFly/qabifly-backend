from django.contrib import admin
from .models import OTPRecord, RefreshTokenRecord


@admin.register(OTPRecord)
class OTPRecordAdmin(admin.ModelAdmin):
    list_display  = ("identifier", "otp_type", "is_used", "attempts", "created_at", "expires_at")
    list_filter   = ("otp_type", "is_used")
    search_fields = ("identifier",)
    readonly_fields = ("id", "otp_code", "created_at")


@admin.register(RefreshTokenRecord)
class RefreshTokenRecordAdmin(admin.ModelAdmin):
    list_display  = ("user", "is_revoked", "created_at", "expires_at")
    list_filter   = ("is_revoked",)
    search_fields = ("user__email",)
    readonly_fields = ("id", "created_at")