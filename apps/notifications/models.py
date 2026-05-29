import uuid
from django.db import models
from django.conf import settings


class Notification(models.Model):

    class NotifType(models.TextChoices):
        ORDER_UPDATE   = "ORDER_UPDATE",   "Order Update"
        PAYMENT        = "PAYMENT",        "Payment"
        DELIVERY       = "DELIVERY",       "Delivery"
        WEATHER_ALERT  = "WEATHER_ALERT",  "Weather Alert"
        UDHAAR_REMINDER = "UDHAAR_REMINDER", "Udhaar Reminder"
        EMI_REMINDER   = "EMI_REMINDER",   "EMI Reminder"
        CHAT           = "CHAT",           "Chat Message"
        BROADCAST      = "BROADCAST",      "Admin Broadcast"
        SYSTEM         = "SYSTEM",         "System"

    class Priority(models.TextChoices):
        NORMAL = "NORMAL", "Normal"
        HIGH   = "HIGH",   "High"
        URGENT = "URGENT", "Urgent"

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient    = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    notif_type   = models.CharField(max_length=25, choices=NotifType.choices)
    priority     = models.CharField(
        max_length=10, choices=Priority.choices, default=Priority.NORMAL
    )
    title        = models.CharField(max_length=200)
    body         = models.TextField()
    data         = models.JSONField(default=dict, blank=True)  # extra payload
    is_read      = models.BooleanField(default=False)
    read_at      = models.DateTimeField(null=True, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notifications"
        ordering = ["-created_at"]
        indexes  = [
            models.Index(fields=["recipient", "is_read"]),
        ]

    def __str__(self):
        return f"{self.notif_type} → {self.recipient.email} — {'read' if self.is_read else 'unread'}"

    def mark_read(self):
        from django.utils import timezone
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=["is_read", "read_at"])