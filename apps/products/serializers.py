from rest_framework import serializers
from apps.users.serializers import PublicUserSerializer
from .models import (
    Product,
    ProductCategory,
    ProductImage,
    ProductVariant,
    ProductReview,
)


class ProductCategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    icon = serializers.SerializerMethodField()

    class Meta:
        model = ProductCategory
        fields = ("id", "name", "slug", "icon", "sort_order", "children")

    def get_icon(self, obj):
        if not obj.icon:
            return None

        request = self.context.get("request")
        url = obj.icon.url

        return request.build_absolute_uri(url) if request else url

    def get_children(self, obj):
        return ProductCategorySerializer(
            obj.children.filter(is_active=True),
            many=True,
            context=self.context,
        ).data


class ProductImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = ("id", "image", "is_primary", "sort_order")
        read_only_fields = ("id",)

    def get_image(self, obj):
        if not obj.image:
            return None

        request = self.context.get("request")
        url = obj.image.url

        return request.build_absolute_uri(url) if request else url


class ProductVariantSerializer(serializers.ModelSerializer):
    price = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariant
        fields = ("id", "name", "price", "stock", "is_active")
        read_only_fields = ("id",)

    def get_price(self, obj):
        return str(obj.price)


class ProductReviewSerializer(serializers.ModelSerializer):
    user = PublicUserSerializer(read_only=True)

    class Meta:
        model = ProductReview
        fields = ("id", "user", "rating", "comment", "created_at")
        read_only_fields = ("id", "user", "created_at")


class ProductCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = (
            "name",
            "category",
            "description",
            "price",
            "discount_percent",
            "stock",
            "low_stock_alert",
            "is_featured",
            "unit",
        )

    def validate(self, attrs):
        request = self.context["request"]

        try:
            shop = request.user.shop
        except Exception:
            raise serializers.ValidationError(
                "You do not have a registered shop."
            )

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
    primary_image = serializers.SerializerMethodField()
    category_name = serializers.CharField(source="category.name", read_only=True)
    shop_name = serializers.CharField(source="shop.name", read_only=True)
    shop_slug = serializers.CharField(source="shop.slug", read_only=True)
    price = serializers.SerializerMethodField()
    discounted_price = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    is_in_stock = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "slug",
            "category_name",
            "shop_name",
            "shop_slug",
            "price",
            "discount_percent",
            "discounted_price",
            "stock",
            "is_in_stock",
            "is_featured",
            "unit",
            "average_rating",
            "total_reviews",
            "primary_image",
            "status",
        )

    def get_price(self, obj):
        return str(obj.price)

    def get_discounted_price(self, obj):
        return str(obj.discounted_price)

    def get_average_rating(self, obj):
        return str(obj.average_rating)

    def get_is_in_stock(self, obj):
        return obj.is_in_stock

    def get_primary_image(self, obj):
        img = obj.images.filter(is_primary=True).first()

        if not img:
            img = obj.images.first()

        if not img or not img.image:
            return None

        request = self.context.get("request")
        url = img.image.url

        return request.build_absolute_uri(url) if request else url


class ProductDetailSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()
    variants = ProductVariantSerializer(many=True, read_only=True)
    reviews = ProductReviewSerializer(many=True, read_only=True)
    category = ProductCategorySerializer(read_only=True)

    shop_name = serializers.CharField(source="shop.name", read_only=True)
    shop_slug = serializers.CharField(source="shop.slug", read_only=True)

    price = serializers.SerializerMethodField()
    discounted_price = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()

    is_in_stock = serializers.SerializerMethodField()
    is_low_stock = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "category",
            "shop_name",
            "shop_slug",
            "price",
            "discount_percent",
            "discounted_price",
            "stock",
            "is_in_stock",
            "is_low_stock",
            "is_featured",
            "unit",
            "status",
            "average_rating",
            "total_reviews",
            "total_sold",
            "images",
            "variants",
            "reviews",
            "created_at",
        )

    def get_price(self, obj):
        return str(obj.price)

    def get_discounted_price(self, obj):
        return str(obj.discounted_price)

    def get_average_rating(self, obj):
        return str(obj.average_rating)

    def get_is_in_stock(self, obj):
        return obj.is_in_stock

    def get_is_low_stock(self, obj):
        return obj.is_low_stock

    def get_images(self, obj):
        images = obj.images.all()
        return ProductImageSerializer(
            images,
            many=True,
            context=self.context,
        ).data


class ProductUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = (
            "description",
            "price",
            "discount_percent",
            "stock",
            "low_stock_alert",
            "is_featured",
            "unit",
            "status",
        )
