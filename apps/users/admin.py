from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("email", "full_name", "role", "is_verified", "is_active", "created_at")
    list_filter = ("role", "is_verified", "is_active", "is_phone_verified")
    search_fields = ("email", "full_name", "phone")
    ordering = ("-created_at",)
    readonly_fields = ("id", "created_at", "updated_at")

    fieldsets = (
        ("Login Info", {"fields": ("id", "email", "password")}),
        ("Personal Info", {"fields": ("full_name", "phone", "date_of_birth", "profile_photo")}),
        ("Role & Status", {"fields": ("role", "is_active", "is_verified", "is_phone_verified")}),
        ("Address", {"fields": ("city", "district", "state", "pincode")}),
        ("Permissions", {"fields": ("is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "password1", "password2", "role"),
        }),
    )