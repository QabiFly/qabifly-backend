import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator


class Wallet(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user       = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wallet",
    )
    balance    = models.DecimalField(
        max_digits=12, decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)],
    )
    # Lifetime stats — never reset
    total_earned   = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_spent    = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_withdrawn = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wallets"

    def __str__(self):
        return f"Wallet — {self.user.email} — ₹{self.balance}"

    def credit(self, amount, description="", reference=""):
        """Add money to wallet. Always use this — never update balance directly."""
        if amount <= 0:
            raise ValueError("Credit amount must be positive.")
        self.balance      += amount
        self.total_earned += amount
        self.save(update_fields=["balance", "total_earned", "updated_at"])
        return WalletTransaction.objects.create(
            wallet      = self,
            txn_type    = WalletTransaction.TxnType.CREDIT,
            amount      = amount,
            balance_after = self.balance,
            description = description,
            reference   = reference,
        )

    def debit(self, amount, description="", reference=""):
        """Remove money from wallet. Raises if insufficient balance."""
        if amount <= 0:
            raise ValueError("Debit amount must be positive.")
        if self.balance < amount:
            raise ValueError(f"Insufficient wallet balance. Available: ₹{self.balance}")
        self.balance     -= amount
        self.total_spent += amount
        self.save(update_fields=["balance", "total_spent", "updated_at"])
        return WalletTransaction.objects.create(
            wallet      = self,
            txn_type    = WalletTransaction.TxnType.DEBIT,
            amount      = amount,
            balance_after = self.balance,
            description = description,
            reference   = reference,
        )


class WalletTransaction(models.Model):

    class TxnType(models.TextChoices):
        CREDIT     = "CREDIT",     "Credit"
        DEBIT      = "DEBIT",      "Debit"
        WITHDRAWAL = "WITHDRAWAL", "Withdrawal"
        REFUND     = "REFUND",     "Refund"

    class TxnSource(models.TextChoices):
        ORDER_PAYMENT  = "ORDER_PAYMENT",  "Order Payment"
        ORDER_REFUND   = "ORDER_REFUND",   "Order Refund"
        DELIVERY_EARN  = "DELIVERY_EARN",  "Delivery Earning"
        SHOP_EARNING   = "SHOP_EARNING",   "Shop Earning"
        TOPUP          = "TOPUP",          "Manual Top-up"
        WITHDRAWAL     = "WITHDRAWAL",     "Withdrawal"
        UDHAAR_COLLECT = "UDHAAR_COLLECT", "Udhaar Collection"
        EMI_PAYMENT    = "EMI_PAYMENT",    "EMI Payment"
        ADMIN_CREDIT   = "ADMIN_CREDIT",   "Admin Credit"

    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wallet        = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name="transactions")
    txn_type      = models.CharField(max_length=20, choices=TxnType.choices)
    source        = models.CharField(
        max_length=30, choices=TxnSource.choices,
        default=TxnSource.TOPUP,
    )
    amount        = models.DecimalField(max_digits=10, decimal_places=2)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2)
    description   = models.CharField(max_length=255, blank=True)
    reference     = models.CharField(max_length=100, blank=True)  # order number / split ID
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "wallet_transactions"
        ordering = ["-created_at"]
        # Transactions are immutable — no update allowed
        managed  = True

    def __str__(self):
        return f"{self.txn_type} ₹{self.amount} — {self.wallet.user.email}"


class WithdrawalRequest(models.Model):

    class Status(models.TextChoices):
        PENDING   = "PENDING",   "Pending"
        PROCESSED = "PROCESSED", "Processed"
        REJECTED  = "REJECTED",  "Rejected"

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wallet      = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name="withdrawals")
    amount      = models.DecimalField(max_digits=10, decimal_places=2)
    upi_id      = models.CharField(max_length=100)
    status      = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    note        = models.TextField(blank=True)
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="processed_withdrawals",
    )
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "withdrawal_requests"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Withdrawal ₹{self.amount} — {self.wallet.user.email} — {self.status}"