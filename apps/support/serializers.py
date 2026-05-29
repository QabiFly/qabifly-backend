import random
import string
from rest_framework import serializers
from .models import SupportTicket, SupportMessage


def generate_ticket_number():
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"TKT-{suffix}"


class SupportMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()

    class Meta:
        model  = SupportMessage
        fields = ("id", "sender_name", "sender_type", "body", "created_at")
        read_only_fields = ("id", "sender_type", "created_at")

    def get_sender_name(self, obj):
        if obj.sender_type == SupportMessage.SenderType.AI:
            return "QabiFly Assistant"
        return obj.sender.full_name if obj.sender else "Unknown"


class SupportTicketListSerializer(serializers.ModelSerializer):
    raised_by_name  = serializers.CharField(source="raised_by.full_name", read_only=True)
    assigned_to_name = serializers.CharField(
        source="assigned_to.full_name", read_only=True, default=""
    )
    message_count   = serializers.IntegerField(source="messages.count", read_only=True)

    class Meta:
        model  = SupportTicket
        fields = (
            "id", "ticket_number", "subject", "category",
            "status", "priority",
            "raised_by_name", "assigned_to_name",
            "message_count", "rating",
            "created_at", "resolved_at",
        )


class SupportTicketDetailSerializer(serializers.ModelSerializer):
    messages        = SupportMessageSerializer(many=True, read_only=True)
    raised_by_name  = serializers.CharField(source="raised_by.full_name", read_only=True)
    assigned_to_name = serializers.CharField(
        source="assigned_to.full_name", read_only=True, default=""
    )

    class Meta:
        model  = SupportTicket
        fields = (
            "id", "ticket_number", "subject", "category",
            "status", "priority",
            "raised_by_name", "assigned_to_name",
            "related_order",
            "rating", "rating_comment",
            "messages", "created_at", "resolved_at",
        )


class CreateTicketSerializer(serializers.Serializer):
    subject       = serializers.CharField(max_length=255)
    category      = serializers.ChoiceField(
        choices=["ORDER", "PAYMENT", "DELIVERY", "ACCOUNT", "UDHAAR", "OTHER"]
    )
    message       = serializers.CharField(min_length=10)
    related_order = serializers.CharField(required=False, allow_blank=True)
    priority      = serializers.ChoiceField(
        choices=["LOW", "MEDIUM", "HIGH"], default="MEDIUM"
    )


class ReplyTicketSerializer(serializers.Serializer):
    message = serializers.CharField(min_length=2)


class RateTicketSerializer(serializers.Serializer):
    rating  = serializers.IntegerField(min_value=1, max_value=5)
    comment = serializers.CharField(required=False, allow_blank=True)


class AdminAssignTicketSerializer(serializers.Serializer):
    agent_id = serializers.UUIDField()