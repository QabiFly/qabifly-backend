import uuid
from django.db import models
from django.conf import settings
from apps.shops.models import Shop


class UdhaarRecord(models.Model):

    class Status(models.TextChoices):
        ACTIVE   = "ACTIVE",   "Active"
        OVERDUE  = "OVERDUE",  "Overdue"
        SETTLED  = "SETTLED",  "Settled"
        PARTIAL  = "PARTIAL",  "Partially Settled"

    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    buyer      = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="udhaar_taken",
    )
    shop       = models.ForeignKey(
        Shop, on_delete=models.PROTECT,
        related_name="udhaar_given",
    )
    order      = models.OneToOneField(
        "orders.Order", on_delete=models.PROTECT,
        related_name="udhaar_record",
        null=True, blank=True,
    )
    amount          = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid     = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    due_date        = models.DateField()
    status          = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ACTIVE
    )
    notes           = models.TextField(blank=True)
    is_settled      = models.BooleanField(default=False)
    settled_at      = models.DateTimeField(null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "udhaar_records"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Udhaar ₹{self.amount} — {self.buyer.full_name} → {self.shop.name}"

    @property
    def amount_remaining(self):
        return round(self.amount - self.amount_paid, 2)

    @property
    def is_overdue_check(self):
        from django.utils import timezone
        return (
            not self.is_settled
            and timezone.now().date() > self.due_date
        )


class UdhaarPayment(models.Model):
    """
    Partial ya full payment record.
    Collected in person (cash) ya wallet se.
    """
    class PaymentMode(models.TextChoices):
        CASH   = "CASH",   "Cash"
        WALLET = "WALLET", "Wallet"
        UPI    = "UPI",    "UPI"

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    udhaar      = models.ForeignKey(
        UdhaarRecord, on_delete=models.CASCADE, related_name="payments"
    )
    amount      = models.DecimalField(max_digits=10, decimal_places=2)
    mode        = models.CharField(
        max_length=10, choices=PaymentMode.choices, default=PaymentMode.CASH
    )
    collected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="udhaar_collections",
    )
    utr_number  = models.CharField(max_length=50, blank=True)
    note        = models.TextField(blank=True)
    paid_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "udhaar_payments"
        ordering = ["-paid_at"]

    def __str__(self):
        return f"₹{self.amount} paid for {self.udhaar}"


class SundayCollection(models.Model):
    """
    Delivery boy Sunday ko ghar ghar jaake collect karta hai.
    """
    class Status(models.TextChoices):
        SCHEDULED  = "SCHEDULED",  "Scheduled"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETED  = "COMPLETED",  "Completed"

    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    delivery_boy  = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name="sunday_collections",
        limit_choices_to={"role": "DELIVERY_BOY"},
    )
    collection_date = models.DateField()
    shop            = models.ForeignKey(
        Shop, on_delete=models.CASCADE, related_name="sunday_collections"
    )
    status          = models.CharField(
        max_length=20, choices=Status.choices, default=Status.SCHEDULED
    )
    total_collected = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_pending   = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    notes           = models.TextField(blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "sunday_collections"
        ordering = ["-collection_date"]

    def __str__(self):
        return f"Sunday Collection {self.collection_date} — {self.shop.name}"