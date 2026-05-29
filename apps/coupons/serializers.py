from rest_framework import serializers
from django.utils import timezone
from .models import Coupon, CouponUsage


class CouponSerializer(serializers.ModelSerializer):
    shop_name    = serializers.CharField(source="shop.name", read_only=True)
    is_valid_now = serializers.BooleanField(read_only=True)

    class Meta:
        model  = Coupon
        fields = (
            "id", "code", "description", "discount_type", "discount_value",
            "shop_name", "min_order_amount", "max_discount_cap",
            "max_uses_total", "max_uses_per_user", "uses_count",
            "is_active", "valid_from", "valid_until",
            "is_valid_now", "created_at",
        )
        read_only_fields = ("id", "uses_count", "created_at")


class CreateCouponSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Coupon
        fields = (
            "code", "description", "discount_type", "discount_value",
            "shop", "min_order_amount", "max_discount_cap",
            "max_uses_total", "max_uses_per_user",
            "is_active", "valid_from", "valid_until",
        )

    def validate_code(self, value):
        return value.upper().strip()

    def validate_valid_until(self, value):
        if value and value < timezone.now():
            raise serializers.ValidationError("Expiry date must be in the future.")
        return value


class ValidateCouponSerializer(serializers.Serializer):
    code         = serializers.CharField()
    order_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    shop_id      = serializers.UUIDField(required=False, allow_null=True)


class CouponUsageSerializer(serializers.ModelSerializer):
    coupon_code  = serializers.CharField(source="coupon.code", read_only=True)
    user_email   = serializers.CharField(source="user.email", read_only=True)
    order_number = serializers.CharField(source="order.order_number", read_only=True)

    class Meta:
        model  = CouponUsage
        fields = (
            "id", "coupon_code", "user_email",
            "order_number", "discount_applied", "used_at",
        )