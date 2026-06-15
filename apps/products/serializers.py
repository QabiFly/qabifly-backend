from rest_framework import serializers
from apps.users.serializers import PublicUserSerializer
from .models import Product, ProductCategory, ProductImage, ProductVariant, ProductReview


class ProductCategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model  = ProductCategory
        fields = ("id", "name", "slug", "icon", "sort_order", "children")

    def get_children(self, obj):
        return ProductCategorySerializer(
            obj.children.filter(is_active=True), many=True
        ).data


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ProductImage
        fields = ("id", "image", "is_primary", "sort_order")
        read_only_fields = ("id",)


class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ProductVariant
        fields = ("id", "name", "price", "stock", "is_active")
        read_only_fields = ("id",)


class ProductReviewSerializer(serializers.ModelSerializer):
    user = PublicUserSerializer(read_only=True)

    class Meta:
        model  = ProductReview
        fields = ("id", "user", "rating", "comment", "created_at")
        read_only_fields = ("id", "user", "created_at")


class ProductCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Product
        fields = (
            "name", "category", "description",
            "price", "discount_percent",
            "stock", "low_stock_alert",
            "is_featured", "unit",
        )

    def validate(self, attrs):
        request = self.context["request"]
        try:
            shop = request.user.shop
        except Exception:
            raise serializers.ValidationError("You do not have a registered shop.")
        if shop.status != "ACTIVE":
            raise serializers.ValidationError(
                "Your shop must be approved before adding products."
            )
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        shop = request.user.shop
        return Product.objects.create(shop=shop, **validated_data)

class ProductListSerializer(serializers.ModelSerializer):
    primary_image    = serializers.SerializerMethodField()
    category_name    = serializers.CharField(source="category.name", read_only=True)
    shop_name        = serializers.CharField(source="shop.name", read_only=True)
    shop_slug        = serializers.CharField(source="shop.slug", read_only=True)  # ← ADD
    discounted_price = serializers.SerializerMethodField()
    is_in_stock      = serializers.SerializerMethodField()  # ← ADD

    class Meta:
        model  = Product
        fields = (
            "id", "name", "slug", "category_name",
            "shop_name", "shop_slug",             # ← ADD shop_slug
            "price", "discount_percent", "discounted_price",
            "stock", "is_in_stock",               # ← ADD is_in_stock
            "is_featured", "unit",
            "average_rating", "total_reviews",
            "primary_image", "status",
        )

    def get_discounted_price(self, obj):
        return str(obj.discounted_price)

    def get_is_in_stock(self, obj):          # ← ADD
        return obj.stock > 0

    def get_primary_image(self, obj):
        img = obj.images.filter(is_primary=True).first()
        if not img:
            img = obj.images.first()  # ← Koi bhi image lo
        if img:
            request = self.context.get("request")
            return request.build_absolute_uri(img.image.url) if request else img.image.url
        return None

class ProductDetailSerializer(serializers.ModelSerializer):
    """Full detail — for product page."""
    images           = ProductImageSerializer(many=True, read_only=True)
    variants         = ProductVariantSerializer(many=True, read_only=True)
    reviews          = ProductReviewSerializer(many=True, read_only=True)
    category         = ProductCategorySerializer(read_only=True)
    discounted_price = serializers.SerializerMethodField()
    shop_name        = serializers.CharField(source="shop.name", read_only=True)
    shop_slug        = serializers.CharField(source="shop.slug", read_only=True)

    # ✅ Sahi tareeka
    is_in_stock      = serializers.SerializerMethodField()
    is_low_stock     = serializers.SerializerMethodField()

    class Meta:
        model  = Product
        fields = (
            "id", "name", "slug", "description",
            "category", "shop_name", "shop_slug",
            "price", "discount_percent", "discounted_price",
            "stock", "is_in_stock", "is_low_stock",
            "is_featured", "unit", "status",
            "average_rating", "total_reviews", "total_sold",
            "images", "variants", "reviews",
            "created_at",
        )

    def get_is_in_stock(self, obj):
        return obj.is_in_stock

    def get_is_low_stock(self, obj):
        return obj.is_low_stock

    def get_discounted_price(self, obj):
        return str(obj.discounted_price)


class ProductUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Product
        fields = (
            "description", "price", "discount_percent",
            "stock", "low_stock_alert",
            "is_featured", "unit", "status",
        )
