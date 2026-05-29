from rest_framework import serializers
from .models import Payment, PaymentSplit


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Payment
        fields = (
            "id", "order", "method", "status", "amount",
            "upi_id", "utr_number", "upi_deep_link",
            "verified_at", "failure_reason", "created_at",
        )
        read_only_fields = (
            "id", "upi_id", "upi_deep_link",
            "verified_at", "created_at",
        )


class UPIDeepLinkSerializer(serializers.Serializer):
    order_number = serializers.CharField()


class SubmitUTRSerializer(serializers.Serializer):
    order_number = serializers.CharField()
    utr_number   = serializers.CharField(
        min_length=6, max_length=50,
        help_text="UTR / Transaction ID from your UPI app"
    )


class AdminVerifyPaymentSerializer(serializers.Serializer):
    action         = serializers.ChoiceField(choices=["verify", "reject"])
    failure_reason = serializers.CharField(required=False, allow_blank=True)


class PaymentSplitSerializer(serializers.ModelSerializer):
    recipient_email = serializers.CharField(source="recipient.email", read_only=True)

    class Meta:
        model  = PaymentSplit
        fields = ("id", "recipient_email", "role", "amount", "percent", "is_credited", "credited_at")