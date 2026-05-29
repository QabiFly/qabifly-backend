from rest_framework import serializers
from .models import Landmark, DeliveryZone


class LandmarkSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Landmark
        fields = (
            "id", "name", "landmark_type",
            "latitude", "longitude",
            "description", "village", "is_active", "created_at",
        )
        read_only_fields = ("id", "created_at")


class DeliveryZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model  = DeliveryZone
        fields = (
            "id", "name", "center_lat", "center_lon",
            "radius_km", "is_active", "color_hex",
            "description", "created_at",
        )
        read_only_fields = ("id", "created_at")


class CheckPointInZoneSerializer(serializers.Serializer):
    latitude  = serializers.DecimalField(max_digits=9, decimal_places=6)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6)