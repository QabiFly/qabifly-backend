from django.contrib import admin
from .models import SupportTicket, SupportMessage


class SupportMessageInline(admin.TabularInline):
    model = SupportMessage
    extra = 0
    readonly_fields = ("sender", "sender_type", "created_at")


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display  = ("ticket_number", "raised_by", "category", "status",
                      "priority", "assigned_to", "created_at")
    list_filter   = ("status", "category", "priority")
    search_fields = ("ticket_number", "raised_by__email", "subject")
    readonly_fields = ("id", "ticket_number", "created_at", "resolved_at")
    inlines = [SupportMessageInline]