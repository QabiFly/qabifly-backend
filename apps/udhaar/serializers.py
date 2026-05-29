from rest_framework import serializers
from apps.users.serializers import PublicUserSerializer
from .models import UdhaarRecord, UdhaarPayment, SundayCollection


class UdhaarPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model  = UdhaarPayment
        fields = (
            "id", "amount", "mode", "collected_by",
            "utr_number", "note", "paid_at",
        )
        read_only_fields = ("id", "paid_at", "collected_by")


class UdhaarRecordSerializer(serializers.ModelSerializer):
    buyer_name      = serializers.CharField(source="buyer.full_name", read_only=True)
    buyer_phone     = serializers.CharField(source="buyer.phone", read_only=True)
    shop_name       = serializers.CharField(source="shop.name", read_only=True)
    amount_remaining = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    payments        = UdhaarPaymentSerializer(many=True, read_only=True)
    is_overdue      = serializers.BooleanField(source="is_overdue_check", read_only=True)

    class Meta:
        model  = UdhaarRecord
        fields = (
            "id", "buyer_name", "buyer_phone", "shop_name",
            "order", "amount", "amount_paid", "amount_remaining",
            "due_date", "status", "is_overdue",
            "notes", "is_settled", "settled_at",
            "payments", "created_at",
        )
        read_only_fields = (
            "id", "amount_paid", "is_settled",
            "settled_at", "created_at",
        )


class RecordUdhaarPaymentSerializer(serializers.Serializer):
    udhaar_id  = serializers.UUIDField()
    amount     = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=1)
    mode       = serializers.ChoiceField(choices=["CASH", "WALLET", "UPI"])
    utr_number = serializers.CharField(required=False, allow_blank=True)
    note       = serializers.CharField(required=False, allow_blank=True)


class SundayCollectionSerializer(serializers.ModelSerializer):
    delivery_boy_name = serializers.CharField(
        source="delivery_boy.full_name", read_only=True
    )
    shop_name = serializers.CharField(source="shop.name", read_only=True)

    class Meta:
        model  = SundayCollection
        fields = (
            "id", "delivery_boy_name", "shop_name",
            "collection_date", "status",
            "total_collected", "total_pending", "notes",
            "created_at",
        )
        read_only_fields = ("id", "created_at")


class CreateSundayCollectionSerializer(serializers.Serializer):
    shop_id         = serializers.UUIDField()
    collection_date = serializers.DateField()
    delivery_boy_id = serializers.UUIDField()