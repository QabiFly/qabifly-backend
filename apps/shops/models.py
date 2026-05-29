import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class ShopCategory(models.Model):
    name        = models.CharField(max_length=100, unique=True)
    slug        = models.SlugField(max_length=100, unique=True)
    icon        = models.ImageField(upload_to="shop_categories/", blank=True, null=True)
    description = models.TextField(blank=True)
    is_active   = models.BooleanField(default=True)
    sort_order  = models.IntegerField(default=0)

    class Meta:
        db_table  = "shop_categories"
        ordering  = ["sort_order", "name"]
        verbose_name_plural = "Shop Categories"

    def __str__(self):
        return self.name


class Shop(models.Model):

    class Status(models.TextChoices):
        PENDING  = "PENDING",  "Pending Approval"
        ACTIVE   = "ACTIVE",   "Active"
        INACTIVE = "INACTIVE", "Inactive"
        REJECTED = "REJECTED", "Rejected"
        BANNED   = "BANNED",   "Banned"

    id       = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner    = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="shop",
        limit_choices_to={"role": "SHOPKEEPER"},
    )
    category = models.ForeignKey(
        ShopCategory,
        on_delete=models.PROTECT,
        related_name="shops",
    )

    # Basic Info
    name        = models.CharField(max_length=200)
    slug        = models.SlugField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    logo        = models.ImageField(upload_to="shops/logos/", blank=True, null=True)
    banner      = models.ImageField(upload_to="shops/banners/", blank=True, null=True)

    # Location — latitude/longitude for 2km radius filtering
    address     = models.TextField()
    village     = models.CharField(max_length=100, default="Reoti")
    block       = models.CharField(max_length=100, default="Reoti")
    district    = models.CharField(max_length=100, default="Ballia")
    state       = models.CharField(max_length=100, default="Uttar Pradesh")
    pincode     = models.CharField(max_length=10, default="221716")
    latitude    = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    longitude   = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )

    # Status & Verification
    status          = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    rejection_reason = models.TextField(blank=True)
    is_open         = models.BooleanField(default=True)  # shopkeeper manually open/close

    # Business Info
    gstin           = models.CharField(max_length=20, blank=True)
    opening_time    = models.TimeField(null=True, blank=True)
    closing_time    = models.TimeField(null=True, blank=True)

    # Stats (denormalized for performance)
    total_orders    = models.IntegerField(default=0)
    total_earnings  = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    average_rating  = models.DecimalField(
        max_digits=3, decimal_places=2, default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    total_reviews   = models.IntegerField(default=0)

    # Admin
    approved_by  = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="approved_shops",
    )
    approved_at  = models.DateTimeField(null=True, blank=True)

    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "shops"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.status})"

    @property
    def is_active(self):
        return self.status == self.Status.ACTIVE

    @property
    def can_accept_orders(self):
        return self.status == self.Status.ACTIVE and self.is_open


class ShopDocument(models.Model):
    """Verification documents uploaded during shop registration."""

    class DocType(models.TextChoices):
        AADHAR        = "AADHAR",        "Aadhaar Card"
        PAN           = "PAN",           "PAN Card"
        GSTIN         = "GSTIN",         "GSTIN Certificate"
        SHOP_PHOTO    = "SHOP_PHOTO",    "Shop Photo"
        OTHER         = "OTHER",         "Other"

    id       = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shop     = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="documents")
    doc_type = models.CharField(max_length=20, choices=DocType.choices)
    file     = models.FileField(upload_to="shops/documents/")
    is_verified = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "shop_documents"

    def __str__(self):
        return f"{self.shop.name} — {self.doc_type}"