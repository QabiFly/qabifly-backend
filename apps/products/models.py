import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.shops.models import Shop


class ProductCategory(models.Model):
    name        = models.CharField(max_length=100)
    slug        = models.SlugField(max_length=100, unique=True)
    parent      = models.ForeignKey(
        "self", on_delete=models.CASCADE,
        null=True, blank=True, related_name="children"
    )
    icon        = models.ImageField(upload_to="product_categories/", blank=True, null=True)
    is_active   = models.BooleanField(default=True)
    sort_order  = models.IntegerField(default=0)

    class Meta:
        db_table  = "product_categories"
        ordering  = ["sort_order", "name"]
        verbose_name_plural = "Product Categories"

    def __str__(self):
        return self.name


class Product(models.Model):

    class Status(models.TextChoices):
        ACTIVE        = "ACTIVE",        "Active"
        INACTIVE      = "INACTIVE",      "Inactive"
        OUT_OF_STOCK  = "OUT_OF_STOCK",  "Out of Stock"
        DELETED       = "DELETED",       "Deleted"

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shop        = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="products")
    category    = models.ForeignKey(
        ProductCategory, on_delete=models.PROTECT, related_name="products"
    )

    # Basic Info
    name        = models.CharField(max_length=255)
    slug        = models.SlugField(max_length=255)
    description = models.TextField(blank=True)
    status      = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ACTIVE
    )

    # Pricing
    price           = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    discount_percent = models.IntegerField(
        default=0, validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    # Stock
    stock           = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    low_stock_alert = models.IntegerField(default=5)  # alert when stock <= this

    # Display
    is_featured = models.BooleanField(default=False)
    unit        = models.CharField(max_length=50, blank=True, default="piece")

    # Stats
    total_sold     = models.IntegerField(default=0)
    average_rating = models.DecimalField(
        max_digits=3, decimal_places=2, default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    total_reviews  = models.IntegerField(default=0)

    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table        = "products"
        ordering        = ["-created_at"]
        unique_together = [("shop", "slug")]

    def __str__(self):
        return f"{self.name} — {self.shop.name}"

   @property
    def discounted_price(self):
        if self.discount_percent > 0:
            # 🔥 FIX: 100 ko Decimal("100") likha taaki division ke baad result Decimal hi rahe
            discount = (self.price * self.discount_percent) / Decimal("100")
            return round(self.price - discount, 2)
        return self.price

    @property
    def is_in_stock(self):
        return self.stock > 0

    @property
    def is_low_stock(self):
        return 0 < self.stock <= self.low_stock_alert

    def deduct_stock(self, quantity: int):
        """Called when order is placed. Auto marks out_of_stock."""
        if quantity > self.stock:
            raise ValueError(f"Insufficient stock for {self.name}")
        self.stock -= quantity
        if self.stock == 0:
            self.status = self.Status.OUT_OF_STOCK
        self.save(update_fields=["stock", "status"])

    def restore_stock(self, quantity: int):
        """Called when order is cancelled."""
        self.stock += quantity
        if self.status == self.Status.OUT_OF_STOCK and self.stock > 0:
            self.status = self.Status.ACTIVE
        self.save(update_fields=["stock", "status"])


class ProductImage(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product    = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image      = models.ImageField(upload_to="products/images/")
    is_primary = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=0)

    class Meta:
        db_table = "product_images"
        ordering = ["sort_order"]

    def save(self, *args, **kwargs):
        # Only one image can be primary per product
        if self.is_primary:
            ProductImage.objects.filter(
                product=self.product, is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)


class ProductVariant(models.Model):
    """Size/colour/weight variants of a product."""
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product    = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    name       = models.CharField(max_length=100)   # e.g. "500g", "Red", "XL"
    price      = models.DecimalField(max_digits=10, decimal_places=2)
    stock      = models.IntegerField(default=0)
    is_active  = models.BooleanField(default=True)

    class Meta:
        db_table = "product_variants"

    def __str__(self):
        return f"{self.product.name} — {self.name}"


class ProductReview(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product    = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    user       = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews"
    )
    rating     = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment    = models.TextField(blank=True)
    is_visible = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table        = "product_reviews"
        unique_together = [("product", "user")]  # one review per user per product
        ordering        = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} — {self.product.name} — {self.rating}★"
