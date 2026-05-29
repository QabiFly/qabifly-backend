from rest_framework import serializers
from apps.products.serializers import ProductListSerializer
from .models import Cart, CartItem


class CartItemSerializer(serializers.ModelSerializer):
    product_name  = serializers.CharField(source="product.name", read_only=True)
    product_slug  = serializers.CharField(source="product.slug", read_only=True)
    variant_name  = serializers.CharField(source="variant.name", read_only=True)
    unit_price    = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    line_total    = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    stock_available = serializers.IntegerField(source="product.stock", read_only=True)
    product_image = serializers.SerializerMethodField()

    class Meta:
        model  = CartItem
        fields = (
            "id", "product", "product_name", "product_slug",
            "product_image", "variant", "variant_name",
            "quantity", "unit_price", "line_total",
            "stock_available", "added_at",
        )
        read_only_fields = ("id", "added_at")

    def get_product_image(self, obj):
        img = obj.product.images.filter(is_primary=True).first()
        if img:
            request = self.context.get("request")
            return request.build_absolute_uri(img.image.url) if request else img.image.url
        return None


class CartSerializer(serializers.ModelSerializer):
    items         = CartItemSerializer(many=True, read_only=True)
    shop_name     = serializers.CharField(source="shop.name", read_only=True)
    shop_slug     = serializers.CharField(source="shop.slug", read_only=True)
    subtotal      = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_items   = serializers.IntegerField(read_only=True)
    delivery_charge = serializers.SerializerMethodField()
    total_amount  = serializers.SerializerMethodField()

    class Meta:
        model  = Cart
        fields = (
            "id", "shop", "shop_name", "shop_slug",
            "items", "total_items", "subtotal",
            "delivery_charge", "total_amount",
            "updated_at",
        )

    def get_delivery_charge(self, obj):
        # Free delivery for now — configurable later
        return 0.00

    def get_total_amount(self, obj):
        return round(obj.subtotal + self.get_delivery_charge(obj), 2)


class AddToCartSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    variant_id = serializers.UUIDField(required=False, allow_null=True)
    quantity   = serializers.IntegerField(min_value=1, max_value=50)


class UpdateCartItemSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1, max_value=50)