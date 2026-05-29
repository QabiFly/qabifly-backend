import uuid
from django.db import models
from django.conf import settings


class SupportTicket(models.Model):

    class Status(models.TextChoices):
        OPEN       = "OPEN",       "Open"
        AI_HANDLED = "AI_HANDLED", "Handled by AI"
        PENDING    = "PENDING",    "Pending Agent"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        RESOLVED   = "RESOLVED",  "Resolved"
        CLOSED     = "CLOSED",    "Closed"

    class Category(models.TextChoices):
        ORDER    = "ORDER",    "Order Issue"
        PAYMENT  = "PAYMENT",  "Payment Issue"
        DELIVERY = "DELIVERY", "Delivery Issue"
        ACCOUNT  = "ACCOUNT",  "Account Issue"
        UDHAAR   = "UDHAAR",   "Udhaar Issue"
        OTHER    = "OTHER",    "Other"

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket_number = models.CharField(max_length=20, unique=True)
    raised_by   = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="support_tickets",
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="assigned_tickets",
        limit_choices_to={"role": "ADMIN"},
    )
    category    = models.CharField(max_length=20, choices=Category.choices)
    subject     = models.CharField(max_length=255)
    status      = models.CharField(
        max_length=20, choices=Status.choices, default=Status.OPEN
    )
    priority    = models.CharField(
        max_length=10,
        choices=[("LOW", "Low"), ("MEDIUM", "Medium"), ("HIGH", "High")],
        default="MEDIUM",
    )
    related_order = models.ForeignKey(
        "orders.Order", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="support_tickets",
    )

    # Rating after resolution
    rating      = models.IntegerField(null=True, blank=True)
    rating_comment = models.TextField(blank=True)

    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "support_tickets"
        ordering = ["-created_at"]

    def __str__(self):
        return f"#{self.ticket_number} — {self.subject} — {self.status}"


class SupportMessage(models.Model):

    class SenderType(models.TextChoices):
        USER  = "USER",  "User"
        AGENT = "AGENT", "Agent / Admin"
        AI    = "AI",    "AI Auto-Response"

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket      = models.ForeignKey(
        SupportTicket, on_delete=models.CASCADE, related_name="messages"
    )
    sender      = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="support_messages",
    )
    sender_type = models.CharField(max_length=10, choices=SenderType.choices)
    body        = models.TextField()
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "support_messages"
        ordering = ["created_at"]

    def __str__(self):
        return f"[{self.sender_type}] {self.ticket.ticket_number} — {self.body[:50]}"