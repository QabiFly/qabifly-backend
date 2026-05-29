import uuid
from django.db import models


class IoTNode(models.Model):
    """
    Physical ESP32 sensor node metadata — PostgreSQL mein.
    Actual readings MongoDB mein jaati hain.
    """

    class Status(models.TextChoices):
        ACTIVE  = "ACTIVE",  "Active"
        STALE   = "STALE",   "Stale"
        OFFLINE = "OFFLINE", "Offline"

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    node_id      = models.CharField(max_length=50, unique=True)  # e.g. REOTI-NODE-01
    name         = models.CharField(max_length=100)
    location     = models.CharField(max_length=200, default="Reoti Block")
    latitude     = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude    = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    status       = models.CharField(
        max_length=10, choices=Status.choices, default=Status.OFFLINE
    )
    last_seen_at = models.DateTimeField(null=True, blank=True)
    firmware_version = models.CharField(max_length=20, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "iot_nodes"
        ordering = ["-last_seen_at"]

    def __str__(self):
        return f"{self.node_id} — {self.status}"