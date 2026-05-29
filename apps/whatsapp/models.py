import uuid
from django.db import models
from django.conf import settings


class WhatsAppSession(models.Model):
    """
    WhatsApp se aane wale users ka session track karta hai.
    Phone number se user identify hota hai.
    """
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone        = models.CharField(max_length=20, unique=True)
    user         = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name="whatsapp_session",
    )
    # Conversation state machine
    state        = models.CharField(
        max_length=50,
        default="IDLE",
        choices=[
            ("IDLE",              "Idle"),
            ("AWAITING_NAME",     "Awaiting Name"),
            ("AWAITING_OTP",      "Awaiting OTP"),
            ("AWAITING_EMAIL",    "Awaiting Email"),
            ("AUTHENTICATED",     "Authenticated"),
            ("ORDER_MENU",        "Order Menu"),
        ],
    )
    temp_data    = models.JSONField(default=dict, blank=True)
    last_msg_at  = models.DateTimeField(auto_now=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "whatsapp_sessions"

    def __str__(self):
        return f"{self.phone} — {self.state}"


class WhatsAppMessage(models.Model):
    """Audit log of all messages sent/received."""

    class Direction(models.TextChoices):
        INBOUND  = "INBOUND",  "Received from user"
        OUTBOUND = "OUTBOUND", "Sent to user"

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session     = models.ForeignKey(
        WhatsAppSession, on_delete=models.CASCADE, related_name="messages"
    )
    direction   = models.CharField(max_length=10, choices=Direction.choices)
    content     = models.TextField()
    wa_msg_id   = models.CharField(max_length=100, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "whatsapp_messages"
        ordering = ["created_at"]

    def __str__(self):
        return f"[{self.direction}] {self.phone_display}: {self.content[:50]}"

    @property
    def phone_display(self):
        return self.session.phone
