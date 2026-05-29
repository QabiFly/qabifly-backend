from rest_framework import serializers
from .models import IoTNode


class IoTNodeSerializer(serializers.ModelSerializer):
    class Meta:
        model  = IoTNode
        fields = (
            "id", "node_id", "name", "location",
            "latitude", "longitude", "status",
            "last_seen_at", "firmware_version", "created_at",
        )
        read_only_fields = ("id", "status", "last_seen_at", "created_at")


class SensorReadingIngestSerializer(serializers.Serializer):
    """ESP32 sends this payload."""
    node_id      = serializers.CharField(max_length=50)
    secret_key   = serializers.CharField(max_length=100)
    temperature  = serializers.FloatField()
    humidity     = serializers.FloatField()
    soil_moisture = serializers.FloatField(required=False, allow_null=True)
    rainfall     = serializers.FloatField(required=False, default=0)
    wind_speed   = serializers.FloatField(required=False, allow_null=True)
    uv_index     = serializers.FloatField(required=False, allow_null=True)


class WeatherResponseSerializer(serializers.Serializer):
    node        = IoTNodeSerializer()
    latest      = serializers.DictField()
    advice      = serializers.ListField(child=serializers.CharField())
    history_24h = serializers.ListField(child=serializers.DictField())