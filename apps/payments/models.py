import uuid
from django.db import models
from django.conf import settings
from apps.orders.models import Order


class Payment(models.Model):

    class Method(models.TextChoices):
        COD    = "COD",    "Cash on Delivery"
        UPI    = "UPI",    "UPI"
        WALLET = "WALLET", "Wallet"
        UDHAAR = "UDHAAR", "Udhaar"

    class Status(models.TextChoices):
        PENDING  = "PENDING",  "Pending"
        PAID     = "PAID",     "Paid"
        FAILED   = "FAILED",   "Failed"
        REFUNDED = "REFUNDED", "Refunded"

    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order          = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="payment")
    method         = models.CharField(max_length=20, choices=Method.choices)
    status         = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    amount         = models.DecimalField(max_digits=10, decimal_places=2)

    # UPI specific
    upi_id         = models.CharField(max_length=100, blank=True)   # merchant UPI ID
    utr_number     = models.CharField(max_length=50, blank=True)    # submitted by user
    upi_deep_link  = models.TextField(blank=True)                   # generated link

    # Admin verification
    verified_by    = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="verified_payments",
    )
    verified_at    = models.DateTimeField(null=True, blank=True)
    failure_reason = models.TextField(blank=True)

    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "payments"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Payment #{self.order.order_number} — {self.method} — {self.status}"


class PaymentSplit(models.Model):
    """
    Automatic payment split after delivery:
    Shopkeeper: 92%, Platform: 5%, Delivery Boy: 3%
    """
    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment        = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name="splits")
    recipient      = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="payment_splits",
    )
    role           = models.CharField(
        max_length=20,
        choices=[("SHOPKEEPER", "Shopkeeper"), ("PLATFORM", "Platform"), ("DELIVERY_BOY", "Delivery Boy")]
    )
    amount         = models.DecimalField(max_digits=10, decimal_places=2)
    percent        = models.DecimalField(max_digits=5, decimal_places=2)
    is_credited    = models.BooleanField(default=False)
    credited_at    = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "payment_splits"

    def __str__(self):
        return f"{self.role} — ₹{self.amount}"