from rest_framework import serializers
from .models import (
    DeliveryBoyProfile, 
    DeliveryAssignment, 
    LocationLog, 
    DeliveryRating
)


# ==================== DELIVERY BOY PROFILE ====================
class DeliveryBoyProfileSerializer(serializers.ModelSerializer):
    user_name    = serializers.CharField(source="user.full_name", read_only=True)
    user_email   = serializers.CharField(source="user.email", read_only=True)
    user_phone   = serializers.CharField(source="user.phone", read_only=True)
    success_rate = serializers.FloatField(read_only=True)

    class Meta:
        model = DeliveryBoyProfile
        fields = (
            "id", "user_name", "user_email", "user_phone",
            "vehicle_type", "vehicle_number",
            "availability", "current_lat", "current_lon",
            "total_deliveries", "successful_deliveries",
            "total_earned", "average_rating", "total_ratings",
            "success_rate", "is_verified", "updated_at",
        )
        read_only_fields = (
            "id", "total_deliveries", "successful_deliveries",
            "total_earned", "average_rating", "total_ratings",
            "success_rate", "updated_at",
        )


# ==================== DELIVERY ASSIGNMENT ====================
class DeliveryAssignmentSerializer(serializers.ModelSerializer):
    order_number     = serializers.CharField(source="order.order_number", read_only=True)
    shop_name        = serializers.CharField(source="order.shop.name", read_only=True)
    shop_lat         = serializers.DecimalField(source="order.shop.latitude", max_digits=9, decimal_places=6, read_only=True)
    shop_lon         = serializers.DecimalField(source="order.shop.longitude", max_digits=9, decimal_places=6, read_only=True)
    delivery_address = serializers.CharField(source="order.delivery_address", read_only=True)
    delivery_lat     = serializers.DecimalField(source="order.delivery_lat", max_digits=9, decimal_places=6, read_only=True)
    delivery_lon     = serializers.DecimalField(source="order.delivery_lon", max_digits=9, decimal_places=6, read_only=True)
    buyer_name       = serializers.CharField(source="order.buyer.full_name", read_only=True)
    buyer_phone      = serializers.CharField(source="order.buyer.phone", read_only=True)
    total_amount     = serializers.DecimalField(source="order.total_amount", max_digits=10, decimal_places=2, read_only=True)
    delivery_otp     = serializers.CharField(source="order.delivery_otp", read_only=True)

    class Meta:
        model = DeliveryAssignment
        fields = (
            "id", "order_number", "status", "earning",
            "shop_name", "shop_lat", "shop_lon",
            "delivery_address", "delivery_lat", "delivery_lon",
            "buyer_name", "buyer_phone", "total_amount",
            "delivery_otp", "distance_km",
            "assigned_at", "accepted_at", "picked_at", "delivered_at",
        )


# ==================== UTILITY SERIALIZERS ====================
class UpdateLocationSerializer(serializers.Serializer):
    latitude  = serializers.DecimalField(max_digits=9, decimal_places=6)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6)


class UpdateAvailabilitySerializer(serializers.Serializer):
    availability = serializers.ChoiceField(
        choices=["AVAILABLE", "ON_DELIVERY", "OFFLINE"]
    )


class AdminAssignDeliverySerializer(serializers.Serializer):
    order_number    = serializers.CharField()
    delivery_boy_id = serializers.UUIDField()


# ==================== RATING SERIALIZER ====================
class DeliveryRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryRating
        fields = ("id", "rating", "comment", "created_at")
        read_only_fields = ("id", "created_at")