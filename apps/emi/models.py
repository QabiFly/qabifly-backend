import uuid
from django.db import models
from django.conf import settings
from apps.orders.models import Order


class EMIPlan(models.Model):

    class Status(models.TextChoices):
        ACTIVE    = "ACTIVE",    "Active"
        COMPLETED = "COMPLETED", "Completed"
        DEFAULTED = "DEFAULTED", "Defaulted"
        CANCELLED = "CANCELLED", "Cancelled"

    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    buyer          = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="emi_plans",
    )
    order          = models.OneToOneField(
        Order, on_delete=models.PROTECT, related_name="emi_plan"
    )
    total_amount   = models.DecimalField(max_digits=10, decimal_places=2)
    months         = models.IntegerField()              # 3 to 24
    monthly_amount = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid    = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status         = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ACTIVE
    )
    start_date     = models.DateField()
    end_date       = models.DateField()
    created_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "emi_plans"
        ordering = ["-created_at"]

    def __str__(self):
        return f"EMI — {self.buyer.full_name} — ₹{self.monthly_amount}x{self.months}"

    @property
    def amount_remaining(self):
        return round(self.total_amount - self.amount_paid, 2)

    @property
    def installments_paid(self):
        return self.installments.filter(
            status=EMIInstallment.Status.PAID
        ).count()


class EMIInstallment(models.Model):

    class Status(models.TextChoices):
        PENDING  = "PENDING",  "Pending"
        PAID     = "PAID",     "Paid"
        OVERDUE  = "OVERDUE",  "Overdue"

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plan        = models.ForeignKey(EMIPlan, on_delete=models.CASCADE, related_name="installments")
    month_number = models.IntegerField()   # 1, 2, 3 ...
    amount      = models.DecimalField(max_digits=10, decimal_places=2)
    due_date    = models.DateField()
    paid_at     = models.DateTimeField(null=True, blank=True)
    status      = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    payment_mode = models.CharField(
        max_length=20,
        choices=[("WALLET", "Wallet"), ("UPI", "UPI"), ("CASH", "Cash")],
        blank=True,
    )
    utr_number  = models.CharField(max_length=50, blank=True)

    class Meta:
        db_table        = "emi_installments"
        ordering        = ["month_number"]
        unique_together = [("plan", "month_number")]

    def __str__(self):
        return f"EMI #{self.month_number} — ₹{self.amount} — {self.status}"