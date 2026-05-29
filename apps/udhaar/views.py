import logging
from django.utils import timezone
from django.db import transaction
from django.conf import settings
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from core.responses import success_response, error_response
from core.permissions import IsShopkeeper, IsAdminUser, IsDeliveryBoy
from apps.users.models import User
from apps.shops.models import Shop
from apps.wallet.models import Wallet
from .models import UdhaarRecord, UdhaarPayment, SundayCollection
from .serializers import (
    UdhaarRecordSerializer,
    RecordUdhaarPaymentSerializer,
    SundayCollectionSerializer,
    CreateSundayCollectionSerializer,
)

logger = logging.getLogger("apps")


# ── Buyer ─────────────────────────────────────────────────────────────────────

class MyUdhaarView(generics.ListAPIView):
    """GET /api/v1/udhaar/mine/ — buyer apna udhaar dekhe"""
    permission_classes = [IsAuthenticated]
    serializer_class   = UdhaarRecordSerializer

    def get_queryset(self):
        return UdhaarRecord.objects.filter(
            buyer=self.request.user
        ).select_related("shop", "buyer").prefetch_related("payments")

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        # Auto-mark overdue
        for record in queryset:
            if record.is_overdue_check and record.status == UdhaarRecord.Status.ACTIVE:
                record.status = UdhaarRecord.Status.OVERDUE
                record.save(update_fields=["status"])

        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data)


# ── Shopkeeper ────────────────────────────────────────────────────────────────

class ShopUdhaarListView(generics.ListAPIView):
    """
    GET /api/v1/udhaar/shop/?status=ACTIVE
    Shopkeeper apni shop ka poora udhaar dekhe.
    """
    permission_classes = [IsAuthenticated, IsShopkeeper]
    serializer_class   = UdhaarRecordSerializer

    def get_queryset(self):
        qs = UdhaarRecord.objects.filter(
            shop=self.request.user.shop
        ).select_related("buyer", "shop").prefetch_related("payments")

        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter.upper())
        return qs

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        # Summary stats
        total_outstanding = sum(r.amount_remaining for r in queryset)
        overdue_count = sum(1 for r in queryset if r.is_overdue_check)

        return success_response(data={
            "records": serializer.data,
            "summary": {
                "total_records":     queryset.count(),
                "total_outstanding": float(total_outstanding),
                "overdue_count":     overdue_count,
            }
        })


class RecordUdhaarPaymentView(APIView):
    """
    POST /api/v1/udhaar/pay/
    Shopkeeper ya delivery boy payment record karta hai.
    CASH, WALLET, ya UPI mode mein.
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = RecordUdhaarPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            udhaar = UdhaarRecord.objects.select_for_update().get(
                id=data["udhaar_id"]
            )
        except UdhaarRecord.DoesNotExist:
            return error_response(message="Udhaar record not found.", status_code=404)

        # Only shopkeeper of that shop or admin or delivery boy can record
        user = request.user
        is_authorized = (
            user.role == "ADMIN"
            or (user.role == "SHOPKEEPER" and hasattr(user, "shop") and user.shop == udhaar.shop)
            or user.role == "DELIVERY_BOY"
        )
        if not is_authorized:
            return error_response(
                message="You are not authorized to record this payment.",
                status_code=403,
            )

        if udhaar.is_settled:
            return error_response(message="This udhaar is already settled.", status_code=400)

        amount = data["amount"]
        if amount > udhaar.amount_remaining:
            return error_response(
                message=f"Payment amount ₹{amount} exceeds remaining balance ₹{udhaar.amount_remaining}.",
                status_code=400,
            )

        # Wallet deduction if mode is WALLET
        if data["mode"] == "WALLET":
            buyer_wallet, _ = Wallet.objects.get_or_create(user=udhaar.buyer)
            if buyer_wallet.balance < amount:
                return error_response(
                    message=f"Buyer's wallet balance insufficient. Available: ₹{buyer_wallet.balance}",
                    status_code=400,
                )
            buyer_wallet.debit(
                amount=amount,
                description=f"Udhaar payment to {udhaar.shop.name}",
                reference=str(udhaar.id),
            )
            # Credit shopkeeper wallet
            shop_wallet, _ = Wallet.objects.get_or_create(user=udhaar.shop.owner)
            shop_wallet.credit(
                amount=amount,
                description=f"Udhaar collected from {udhaar.buyer.full_name}",
                reference=str(udhaar.id),
            )

        # Record payment
        payment = UdhaarPayment.objects.create(
            udhaar       = udhaar,
            amount       = amount,
            mode         = data["mode"],
            collected_by = request.user,
            utr_number   = data.get("utr_number", ""),
            note         = data.get("note", ""),
        )

        # Update udhaar record
        udhaar.amount_paid += amount
        if udhaar.amount_remaining <= 0:
            udhaar.is_settled = True
            udhaar.status     = UdhaarRecord.Status.SETTLED
            udhaar.settled_at = timezone.now()
        elif udhaar.amount_paid > 0:
            udhaar.status = UdhaarRecord.Status.PARTIAL

        udhaar.save(update_fields=["amount_paid", "is_settled", "status", "settled_at"])

        logger.info(
            f"Udhaar payment: ₹{amount} by {udhaar.buyer.full_name} "
            f"to {udhaar.shop.name} — mode: {data['mode']}"
        )
        return success_response(
            message=f"₹{amount} payment recorded. Remaining: ₹{udhaar.amount_remaining}",
        )


# ── Sunday Collection ─────────────────────────────────────────────────────────

class CreateSundayCollectionView(APIView):
    """POST /api/v1/udhaar/sunday-collection/create/ — Admin schedules"""
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        serializer = CreateSundayCollectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            shop = Shop.objects.get(id=data["shop_id"])
        except Shop.DoesNotExist:
            return error_response(message="Shop not found.", status_code=404)

        try:
            delivery_boy = User.objects.get(
                id=data["delivery_boy_id"], role="DELIVERY_BOY"
            )
        except User.DoesNotExist:
            return error_response(message="Delivery boy not found.", status_code=404)

        # Calculate total pending for this shop
        pending = UdhaarRecord.objects.filter(
            shop=shop, is_settled=False
        ).aggregate(
            total=__import__("django.db.models", fromlist=["Sum"]).Sum("amount_paid")
        )

        from decimal import Decimal
        total_pending = sum(
            r.amount_remaining
            for r in UdhaarRecord.objects.filter(shop=shop, is_settled=False)
        )

        collection = SundayCollection.objects.create(
            delivery_boy    = delivery_boy,
            collection_date = data["collection_date"],
            shop            = shop,
            total_pending   = total_pending,
        )

        return success_response(
            data=SundayCollectionSerializer(collection).data,
            message="Sunday collection scheduled.",
            status_code=status.HTTP_201_CREATED,
        )


class SundayCollectionListView(generics.ListAPIView):
    """GET /api/v1/udhaar/sunday-collection/"""
    permission_classes = [IsAuthenticated]
    serializer_class   = SundayCollectionSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == "ADMIN":
            return SundayCollection.objects.select_related("delivery_boy", "shop").all()
        elif user.role == "DELIVERY_BOY":
            return SundayCollection.objects.filter(delivery_boy=user)
        elif user.role == "SHOPKEEPER":
            return SundayCollection.objects.filter(shop=user.shop)
        return SundayCollection.objects.none()

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return success_response(data=serializer.data)


class AdminUdhaarOverviewView(APIView):
    """GET /api/v1/udhaar/admin/overview/ — full area udhaar analytics"""
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        all_records = UdhaarRecord.objects.select_related("buyer", "shop")
        total_outstanding = sum(r.amount_remaining for r in all_records if not r.is_settled)
        overdue_records   = [r for r in all_records if r.is_overdue_check]

        return success_response(data={
            "total_active_records":  all_records.filter(is_settled=False).count(),
            "total_outstanding_amount": float(total_outstanding),
            "total_overdue_records": len(overdue_records),
            "total_settled_records": all_records.filter(is_settled=True).count(),
        })