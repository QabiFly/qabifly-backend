from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Notification
        fields = (
            "id", "notif_type", "priority",
            "title", "body", "data",
            "is_read", "read_at", "created_at",
        )
        read_only_fields = ("id", "created_at", "read_at")


class BroadcastSerializer(serializers.Serializer):
    target_role = serializers.ChoiceField(
        choices=["ALL", "BUYER", "SHOPKEEPER", "DELIVERY_BOY", "ADMIN"]
    )
    title       = serializers.CharField(max_length=200)
    body        = serializers.CharField()
    priority    = serializers.ChoiceField(
        choices=["NORMAL", "HIGH", "URGENT"], default="NORMAL"
    )