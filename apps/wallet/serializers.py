from rest_framework import serializers
from .models import Wallet, WalletTransaction, WithdrawalRequest


class WalletSerializer(serializers.ModelSerializer):
    today_earned   = serializers.SerializerMethodField()
    month_earned   = serializers.SerializerMethodField()

    class Meta:
        model  = Wallet
        fields = (
            "id", "balance",
            "total_earned", "total_spent", "total_withdrawn",
            "today_earned", "month_earned",
            "updated_at",
        )

    def get_today_earned(self, obj):
        from django.utils import timezone
        today = timezone.now().date()
        result = obj.transactions.filter(
            txn_type=WalletTransaction.TxnType.CREDIT,
            created_at__date=today,
        ).aggregate(total=__import__("django.db.models",
                    fromlist=["Sum"]).Sum("amount"))["total"]
        return result or 0

    def get_month_earned(self, obj):
        from django.utils import timezone
        now = timezone.now()
        result = obj.transactions.filter(
            txn_type=WalletTransaction.TxnType.CREDIT,
            created_at__year=now.year,
            created_at__month=now.month,
        ).aggregate(total=__import__("django.db.models",
                    fromlist=["Sum"]).Sum("amount"))["total"]
        return result or 0


class WalletTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model  = WalletTransaction
        fields = (
            "id", "txn_type", "source",
            "amount", "balance_after",
            "description", "reference",
            "created_at",
        )


class TopUpSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=10)
    utr_number = serializers.CharField(
        max_length=50,
        help_text="UTR from your UPI payment to 6387403745@fam"
    )


class WithdrawalRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model  = WithdrawalRequest
        fields = (
            "id", "amount", "upi_id", "status",
            "note", "processed_at", "created_at",
        )
        read_only_fields = ("id", "status", "processed_at", "created_at")

    def validate_amount(self, value):
        wallet = self.context["wallet"]
        if value > wallet.balance:
            raise serializers.ValidationError(
                f"Insufficient balance. Available: ₹{wallet.balance}"
            )
        if value < 10:
            raise serializers.ValidationError("Minimum withdrawal is ₹10.")
        return value


class AdminProcessWithdrawalSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=["process", "reject"])
    note   = serializers.CharField(required=False, allow_blank=True)