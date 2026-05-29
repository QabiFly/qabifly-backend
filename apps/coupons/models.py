import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.shops.models import Shop


class Coupon(models.Model):

    class DiscountType(models.TextChoices):
        PERCENTAGE    = "PERCENTAGE",    "Percentage Off"
        FIXED_AMOUNT  = "FIXED_AMOUNT",  "Fixed Amount Off"
        FREE_DELIVERY = "FREE_DELIVERY", "Free Delivery"
        FIRST_ORDER   = "FIRST_ORDER",   "First Order Discount"

    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code            = models.CharField(max_length=50, unique=True)
    description     = models.TextField(blank=True)
    discount_type   = models.CharField(max_length=20, choices=DiscountType.choices)
    discount_value  = models.DecimalField(max_digits=8, decimal_places=2)

    # Scope — null means platform-wide
    shop            = models.ForeignKey(
        Shop, on_delete=models.CASCADE,
        null=True, blank=True, related_name="coupons"
    )

    # Rules
    min_order_amount  = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_discount_cap  = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True,
        help_text="Max discount for percentage type"
    )
    max_uses_total    = models.IntegerField(null=True, blank=True)
    max_uses_per_user = models.IntegerField(default=1)
    uses_count        = models.IntegerField(default=0)

    # Validity
    is_active   = models.BooleanField(default=True)
    valid_from  = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField(null=True, blank=True)

    created_by  = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name="created_coupons",
    )
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "coupons"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.code} — {self.discount_type}"

    @property
    def is_valid_now(self):
        now = timezone.now()
        if not self.is_active:
            return False
        if now < self.valid_from:
            return False
        if self.valid_until and now > self.valid_until:
            return False
        if self.max_uses_total and self.uses_count >= self.max_uses_total:
            return False
        return True

    def calculate_discount(self, subtotal: float) -> float:
        """Calculate actual discount amount for given subtotal."""
        if not self.is_valid_now:
            return 0
        if subtotal < float(self.min_order_amount):
            return 0

        if self.discount_type == self.DiscountType.PERCENTAGE:
            discount = subtotal * float(self.discount_value) / 100
            if self.max_discount_cap:
                discount = min(discount, float(self.max_discount_cap))
            return round(discount, 2)

        elif self.discount_type == self.DiscountType.FIXED_AMOUNT:
            return round(min(float(self.discount_value), subtotal), 2)

        elif self.discount_type in (
            self.DiscountType.FREE_DELIVERY,
            self.DiscountType.FIRST_ORDER,
        ):
            return round(float(self.discount_value), 2)

        return 0


class CouponUsage(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    coupon     = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name="usages")
    user       = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="coupon_usages"
    )
    order      = models.ForeignKey(
        "orders.Order", on_delete=models.CASCADE, related_name="coupon_usages"
    )
    discount_applied = models.DecimalField(max_digits=8, decimal_places=2)
    used_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "coupon_usages"
        ordering = ["-used_at"]

    def __str__(self):
        return f"{self.coupon.code} used by {self.user.email}"