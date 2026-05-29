import logging
from django.utils import timezone
from django.db import transaction
from rest_framework.views import APIView
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated

from core.responses import success_response, error_response
from core.permissions import IsAdminUser
from .models import Wallet, WalletTransaction, WithdrawalRequest
from .serializers import (
    WalletSerializer,
    WalletTransactionSerializer,
    TopUpSerializer,
    WithdrawalRequestSerializer,
    AdminProcessWithdrawalSerializer,
)

logger = logging.getLogger("apps")


class MyWalletView(APIView):
    """GET /api/v1/wallet/ — wallet balance + stats"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        wallet, _ = Wallet.objects.get_or_create(user=request.user)
        return success_response(data=WalletSerializer(wallet).data)


class WalletTransactionsView(generics.ListAPIView):
    """GET /api/v1/wallet/transactions/"""
    permission_classes = [IsAuthenticated]
    serializer_class   = WalletTransactionSerializer

    def get_queryset(self):
        wallet, _ = Wallet.objects.get_or_create(user=self.request.user)
        qs = wallet.transactions.all()

        txn_type = self.request.query_params.get("type")
        source   = self.request.query_params.get("source")
        if txn_type:
            qs = qs.filter(txn_type=txn_type.upper())
        if source:
            qs = qs.filter(source=source.upper())
        return qs

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return success_response(data=serializer.data)


class TopUpWalletView(APIView):
    """
    POST /api/v1/wallet/topup/
    User pehle UPI se 6387403745@fam pe payment karta hai,
    phir UTR submit karta hai → admin verify karega.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TopUpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        amount     = serializer.validated_data["amount"]
        utr_number = serializer.validated_data["utr_number"]

        # Check duplicate UTR
        if WalletTransaction.objects.filter(reference=utr_number).exists():
            return error_response(
                message="This UTR number has already been submitted.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # Create pending topup record — admin will verify
        wallet, _ = Wallet.objects.get_or_create(user=request.user)

        # Store as pending withdrawal request (reuse for topup tracking)
        # We use a separate pending log in description
        WalletTransaction.objects.create(
            wallet        = wallet,
            txn_type      = WalletTransaction.TxnType.CREDIT,
            source        = WalletTransaction.TxnSource.TOPUP,
            amount        = amount,
            balance_after = wallet.balance,  # not yet credited
            description   = f"PENDING TOPUP — UTR: {utr_number}",
            reference     = utr_number,
        )

        logger.info(f"Topup request: ₹{amount} UTR:{utr_number} by {request.user.email}")
        return success_response(
            message=f"Top-up request submitted. Admin will credit ₹{amount} after UTR verification."
        )


class AdminCreditWalletView(APIView):
    """
    POST /api/v1/wallet/admin/credit/
    Admin manually credits wallet after UTR verification.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    @transaction.atomic
    def post(self, request):
        utr_number = request.data.get("utr_number")
        if not utr_number:
            return error_response(message="UTR number required.", status_code=400)

        try:
            pending_txn = WalletTransaction.objects.get(
                reference=utr_number,
                source=WalletTransaction.TxnSource.TOPUP,
            )
        except WalletTransaction.DoesNotExist:
            return error_response(message="No pending topup found for this UTR.", status_code=404)

        if "PENDING" not in pending_txn.description:
            return error_response(message="This UTR is already processed.", status_code=400)

        wallet = pending_txn.wallet
        amount = pending_txn.amount

        # Actually credit
        wallet.credit(
            amount=amount,
            description=f"Wallet topup — UTR: {utr_number}",
            reference=utr_number,
        )

        # Mark pending txn as processed
        pending_txn.description = pending_txn.description.replace("PENDING TOPUP", "PROCESSED TOPUP")
        pending_txn.save(update_fields=["description"])

        return success_response(message=f"₹{amount} credited to {wallet.user.email}'s wallet.")


class RequestWithdrawalView(APIView):
    """POST /api/v1/wallet/withdraw/"""
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        wallet, _ = Wallet.objects.get_or_create(user=request.user)
        serializer = WithdrawalRequestSerializer(
            data=request.data, context={"wallet": wallet}
        )
        serializer.is_valid(raise_exception=True)
        amount = serializer.validated_data["amount"]

        # Hold the amount immediately
        wallet.debit(
            amount=amount,
            description=f"Withdrawal request — UPI: {serializer.validated_data['upi_id']}",
            reference="WITHDRAWAL",
        )
        wallet.total_withdrawn += amount
        wallet.save(update_fields=["total_withdrawn"])

        withdrawal = WithdrawalRequest.objects.create(
            wallet=wallet,
            amount=amount,
            upi_id=serializer.validated_data["upi_id"],
        )

        return success_response(
            data=WithdrawalRequestSerializer(withdrawal).data,
            message=f"Withdrawal request of ₹{amount} submitted. Will be processed within 24 hours.",
            status_code=status.HTTP_201_CREATED,
        )


class MyWithdrawalsView(generics.ListAPIView):
    """GET /api/v1/wallet/withdrawals/"""
    permission_classes = [IsAuthenticated]
    serializer_class   = WithdrawalRequestSerializer

    def get_queryset(self):
        wallet, _ = Wallet.objects.get_or_create(user=self.request.user)
        return wallet.withdrawals.all()

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return success_response(data=serializer.data)


class AdminWithdrawalsView(generics.ListAPIView):
    """GET /api/v1/wallet/admin/withdrawals/"""
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class   = WithdrawalRequestSerializer

    def get_queryset(self):
        qs = WithdrawalRequest.objects.select_related("wallet__user")
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter.upper())
        return qs

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return success_response(data=serializer.data)


class AdminProcessWithdrawalView(APIView):
    """POST /api/v1/wallet/admin/withdrawals/<id>/process/"""
    permission_classes = [IsAuthenticated, IsAdminUser]

    @transaction.atomic
    def post(self, request, withdrawal_id):
        try:
            withdrawal = WithdrawalRequest.objects.select_related(
                "wallet__user"
            ).get(id=withdrawal_id, status=WithdrawalRequest.Status.PENDING)
        except WithdrawalRequest.DoesNotExist:
            return error_response(message="Withdrawal request not found.", status_code=404)

        serializer = AdminProcessWithdrawalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        action = serializer.validated_data["action"]

        if action == "process":
            withdrawal.status       = WithdrawalRequest.Status.PROCESSED
            withdrawal.processed_by = request.user
            withdrawal.processed_at = timezone.now()
            withdrawal.note         = serializer.validated_data.get("note", "")
            withdrawal.save()
            return success_response(
                message=f"Withdrawal of ₹{withdrawal.amount} marked as processed."
            )
        else:
            # Refund back to wallet
            withdrawal.wallet.credit(
                amount=withdrawal.amount,
                description="Withdrawal rejected — amount refunded",
                reference=str(withdrawal.id),
            )
            withdrawal.status = WithdrawalRequest.Status.REJECTED
            withdrawal.note   = serializer.validated_data.get("note", "Rejected by admin")
            withdrawal.save()
            return success_response(
                message=f"Withdrawal rejected. ₹{withdrawal.amount} refunded to wallet."
            )