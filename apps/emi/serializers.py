from rest_framework import serializers
from .models import EMIPlan, EMIInstallment


class EMIInstallmentSerializer(serializers.ModelSerializer):
    class Meta:
        model  = EMIInstallment
        fields = (
            "id", "month_number", "amount",
            "due_date", "status", "paid_at",
            "payment_mode", "utr_number",
        )
        read_only_fields = ("id", "paid_at")


class EMIPlanSerializer(serializers.ModelSerializer):
    installments        = EMIInstallmentSerializer(many=True, read_only=True)
    installments_paid   = serializers.IntegerField(read_only=True)
    amount_remaining    = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    order_number        = serializers.CharField(source="order.order_number", read_only=True)

    class Meta:
        model  = EMIPlan
        fields = (
            "id", "order_number",
            "total_amount", "months", "monthly_amount",
            "amount_paid", "amount_remaining",
            "installments_paid", "status",
            "start_date", "end_date",
            "installments", "created_at",
        )
        read_only_fields = ("id", "created_at")


class CreateEMIPlanSerializer(serializers.Serializer):
    order_number = serializers.CharField()
    months       = serializers.IntegerField(min_value=3, max_value=24)

    def validate_months(self, value):
        allowed = [3, 6, 9, 12, 18, 24]
        if value not in allowed:
            raise serializers.ValidationError(
                f"Months must be one of: {allowed}"
            )
        return value


class PayEMIInstallmentSerializer(serializers.Serializer):
    installment_id = serializers.UUIDField()
    payment_mode   = serializers.ChoiceField(choices=["WALLET", "UPI", "CASH"])
    utr_number     = serializers.CharField(required=False, allow_blank=True)