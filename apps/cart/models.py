import uuid
from django.db import models
from django.conf import settings
from apps.shops.models import Shop
from apps.products.models import Product, ProductVariant


class Cart(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user       = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cart",
    )
    shop       = models.ForeignKey(
        Shop, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="carts",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "carts"

    def __str__(self):
        return f"Cart — {self.user.email}"

    @property
    def total_items(self):
        return self.items.aggregate(
            total=models.Sum("quantity")
        )["total"] or 0

    @property
    def subtotal(self):
        total = sum(item.line_total for item in self.items.all())
        return round(total, 2)

    def clear(self):
        self.items.all().delete()
        self.shop = None
        self.save(update_fields=["shop"])


class CartItem(models.Model):
    id       = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart     = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product  = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="cart_items")
    variant  = models.ForeignKey(
        ProductVariant, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="cart_items",
    )
    quantity = models.IntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table        = "cart_items"
        unique_together = [("cart", "product", "variant")]

    def __str__(self):
        return f"{self.product.name} x{self.quantity}"

    @property
    def unit_price(self):
        if self.variant:
            return self.variant.price
        return self.product.discounted_price

    @property
    def line_total(self):
        return round(self.unit_price * self.quantity, 2)