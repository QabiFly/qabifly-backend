import uuid
from django.db import models
from django.conf import settings
from apps.shops.models import Shop
from apps.products.models import Product, ProductVariant


class Order(models.Model):

    class Status(models.TextChoices):
        PENDING   = "PENDING",   "Pending"
        CONFIRMED = "CONFIRMED", "Confirmed"
        PREPARING = "PREPARING", "Preparing"
        READY     = "READY",     "Ready for Pickup"
        PICKED    = "PICKED",    "Picked Up"
        DELIVERED = "DELIVERED", "Delivered"
        CANCELLED = "CANCELLED", "Cancelled"

    class PaymentMethod(models.TextChoices):
        COD     = "COD",    "Cash on Delivery"
        UPI     = "UPI",    "UPI / Online"
        WALLET  = "WALLET", "QabiFly Wallet"
        UDHAAR  = "UDHAAR", "Udhaar (Credit)"

    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number   = models.CharField(max_length=20, unique=True)
    buyer          = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="orders",
    )
    shop           = models.ForeignKey(
        Shop, on_delete=models.PROTECT, related_name="orders",
    )

    # Status
    status         = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )

    # Payment
    payment_method = models.CharField(
        max_length=20, choices=PaymentMethod.choices, default=PaymentMethod.COD
    )
    payment_status = models.CharField(
        max_length=20,
        choices=[
            ("PENDING",  "Pending"),
            ("PAID",     "Paid"),
            ("FAILED",   "Failed"),
            ("REFUNDED", "Refunded"),
        ],
        default="PENDING",
    )

    # Pricing
    subtotal         = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_charge  = models.DecimalField(max_digits=8,  decimal_places=2, default=0)
    discount_amount  = models.DecimalField(max_digits=8,  decimal_places=2, default=0)
    total_amount     = models.DecimalField(max_digits=10, decimal_places=2)

    # Delivery address (snapshot at order time)
    delivery_address = models.TextField()
    delivery_lat     = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    delivery_lon     = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    # Delivery OTP
    delivery_otp     = models.CharField(max_length=6, blank=True)
    delivery_otp_verified = models.BooleanField(default=False)

    # Coupon
    coupon_code      = models.CharField(max_length=50, blank=True)

    # Notes
    buyer_note       = models.TextField(blank=True)
    cancellation_reason = models.TextField(blank=True)

    # Timestamps
    confirmed_at     = models.DateTimeField(null=True, blank=True)
    delivered_at     = models.DateTimeField(null=True, blank=True)
    cancelled_at     = models.DateTimeField(null=True, blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "orders"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.order_number} — {self.buyer.email}"

    @property
    def can_cancel(self):
        return self.status in (self.Status.PENDING, self.Status.CONFIRMED)

    @property
    def is_delivered(self):
        return self.status == self.Status.DELIVERED


class OrderItem(models.Model):
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order       = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product     = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="order_items")
    variant     = models.ForeignKey(
        ProductVariant, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="order_items",
    )
    
    product_name  = models.CharField(max_length=255)
    variant_name  = models.CharField(max_length=100, blank=True)
    unit_price    = models.DecimalField(max_digits=10, decimal_places=2)
    quantity      = models.IntegerField()
    
    # ✅ Yeh line important hai
    line_total    = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        null=False, 
        blank=False
    )

    class Meta:
        db_table = "order_items"

    def __str__(self):
        return f"{self.product_name} x{self.quantity}"

    # 🔥 Auto Calculate line_total
    def save(self, *args, **kwargs):
        if self.unit_price is not None and self.quantity is not None:
            self.line_total = self.unit_price * self.quantity
        else:
            self.line_total = 0.00
        super().save(*args, **kwargs)


class OrderStatusLog(models.Model):
    """Full audit trail of every status change."""
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order      = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="status_logs")
    from_status = models.CharField(max_length=20, blank=True)
    to_status   = models.CharField(max_length=20)
    changed_by  = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="order_status_changes",
    )
    note        = models.TextField(blank=True)
    changed_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "order_status_logs"
        ordering = ["changed_at"]