from rest_framework import serializers
from .models import Order, OrderItem, OrderStatusLog


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model  = OrderItem
        fields = (
            "id", "product", "variant",
            "product_name", "variant_name",
            "unit_price", "quantity", "line_total",
        )


class OrderStatusLogSerializer(serializers.ModelSerializer):
    changed_by_email = serializers.CharField(
        source="changed_by.email", read_only=True, default=""
    )

    class Meta:
        model  = OrderStatusLog
        fields = ("from_status", "to_status", "changed_by_email", "note", "changed_at")


class OrderListSerializer(serializers.ModelSerializer):
    shop_name    = serializers.CharField(source="shop.name", read_only=True)
    total_items  = serializers.IntegerField(source="items.count", read_only=True)

    class Meta:
        model  = Order
        fields = (
            "id", "order_number", "shop_name", "status",
            "payment_method", "payment_status",
            "total_amount", "total_items",
            "created_at",
        )


class OrderDetailSerializer(serializers.ModelSerializer):
    items       = OrderItemSerializer(many=True, read_only=True)
    status_logs = OrderStatusLogSerializer(many=True, read_only=True)
    shop_name   = serializers.CharField(source="shop.name", read_only=True)
    buyer_email = serializers.CharField(source="buyer.email", read_only=True)
    buyer_name  = serializers.CharField(source="buyer.full_name", read_only=True)

    class Meta:
        model  = Order
        fields = (
            "id", "order_number",
            "buyer_email", "buyer_name", "shop_name",
            "status", "payment_method", "payment_status",
            "subtotal", "delivery_charge", "discount_amount", "total_amount",
            "delivery_address",
            "delivery_otp_verified",
            "coupon_code", "buyer_note",
            "cancellation_reason",
            "confirmed_at", "delivered_at", "cancelled_at", "created_at",
            "items", "status_logs",
        )


class PlaceOrderSerializer(serializers.Serializer):
    payment_method   = serializers.ChoiceField(
        choices=["COD", "UPI", "WALLET", "UDHAAR"]
    )
    delivery_address = serializers.CharField(min_length=10)
    delivery_lat     = serializers.DecimalField(
        max_digits=9, decimal_places=6, required=False, allow_null=True
    )
    delivery_lon     = serializers.DecimalField(
        max_digits=9, decimal_places=6, required=False, allow_null=True
    )
    coupon_code      = serializers.CharField(required=False, allow_blank=True)
    buyer_note       = serializers.CharField(required=False, allow_blank=True)


class CancelOrderSerializer(serializers.Serializer):
    reason = serializers.CharField(min_length=5)


class UpdateOrderStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=["CONFIRMED", "PREPARING", "READY", "PICKED", "DELIVERED", "CANCELLED"]
    )
    note   = serializers.CharField(required=False, allow_blank=True)


class VerifyDeliveryOTPSerializer(serializers.Serializer):
    otp_code = serializers.CharField(min_length=6, max_length=6)