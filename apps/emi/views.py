import logging
from datetime import date
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from django.db import transaction
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from core.responses import success_response, error_response
from core.permissions import IsAdminUser
from apps.orders.models import Order
from apps.wallet.models import Wallet
from .models import EMIPlan, EMIInstallment
from .serializers import (
    EMIPlanSerializer,
    CreateEMIPlanSerializer,
    PayEMIInstallmentSerializer,
)

logger = logging.getLogger("apps")

MINIMUM_EMI_ORDER_AMOUNT = 1000


class CreateEMIPlanView(APIView):
    """
    POST /api/v1/emi/create/
    Rules:
    - Order amount >= ₹1000
    - KYC verified
    - No existing active EMI on same order
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        # KYC check
        if not request.user.is_verified:
            return error_response(
                message="Email verification required for EMI.",
                status_code=403,
            )

        serializer = CreateEMIPlanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            order = Order.objects.get(
                order_number=data["order_number"],
                buyer=request.user,
            )
        except Order.DoesNotExist:
            return error_response(message="Order not found.", status_code=404)

        # Eligibility checks
        if order.total_amount < MINIMUM_EMI_ORDER_AMOUNT:
            return error_response(
                message=f"EMI is available for orders above ₹{MINIMUM_EMI_ORDER_AMOUNT}.",
                status_code=400,
            )

        if hasattr(order, "emi_plan"):
            return error_response(
                message="EMI plan already exists for this order.",
                status_code=400,
            )

        months         = data["months"]
        total_amount   = float(order.total_amount)
        monthly_amount = round(total_amount / months, 2)
        start_date     = timezone.now().date()
        end_date       = start_date + relativedelta(months=months)

        plan = EMIPlan.objects.create(
            buyer          = request.user,
            order          = order,
            total_amount   = total_amount,
            months         = months,
            monthly_amount = monthly_amount,
            start_date     = start_date,
            end_date       = end_date,
        )

        # Create all installment records
        for i in range(1, months + 1):
            due_date = start_date + relativedelta(months=i)
            EMIInstallment.objects.create(
                plan         = plan,
                month_number = i,
                amount       = monthly_amount,
                due_date     = due_date,
            )

        logger.info(f"EMI plan created: {plan} for order #{order.order_number}")
        return success_response(
            data=EMIPlanSerializer(plan).data,
            message=f"EMI plan created. ₹{monthly_amount}/month for {months} months.",
            status_code=status.HTTP_201_CREATED,
        )


class MyEMIPlansView(generics.ListAPIView):
    """GET /api/v1/emi/mine/"""
    permission_classes = [IsAuthenticated]
    serializer_class   = EMIPlanSerializer

    def get_queryset(self):
        return EMIPlan.objects.filter(
            buyer=self.request.user
        ).prefetch_related("installments")

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return success_response(data=serializer.data)


class PayEMIInstallmentView(APIView):
    """
    POST /api/v1/emi/pay/
    Pay a specific installment via WALLET, UPI, or CASH.
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = PayEMIInstallmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            installment = EMIInstallment.objects.select_for_update().select_related(
                "plan__buyer", "plan__order__shop"
            ).get(id=data["installment_id"], plan__buyer=request.user)
        except EMIInstallment.DoesNotExist:
            return error_response(message="Installment not found.", status_code=404)

        if installment.status == EMIInstallment.Status.PAID:
            return error_response(message="This installment is already paid.", status_code=400)

        plan   = installment.plan
        amount = installment.amount

        # Wallet payment
        if data["payment_mode"] == "WALLET":
            buyer_wallet, _ = Wallet.objects.get_or_create(user=request.user)
            if buyer_wallet.balance < amount:
                return error_response(
                    message=f"Insufficient wallet balance. Available: ₹{buyer_wallet.balance}",
                    status_code=400,
                )
            buyer_wallet.debit(
                amount=amount,
                description=f"EMI #{installment.month_number} — Order #{plan.order.order_number}",
                reference=str(installment.id),
            )

            # Credit shopkeeper
            shop_wallet, _ = Wallet.objects.get_or_create(user=plan.order.shop.owner)
            shop_wallet.credit(
                amount=amount,
                description=f"EMI received — Order #{plan.order.order_number}",
                reference=str(installment.id),
            )

        # Mark installment paid
        installment.status       = EMIInstallment.Status.PAID
        installment.paid_at      = timezone.now()
        installment.payment_mode = data["payment_mode"]
        installment.utr_number   = data.get("utr_number", "")
        installment.save()

        # Update plan
        plan.amount_paid += amount
        if plan.amount_paid >= plan.total_amount:
            plan.status = EMIPlan.Status.COMPLETED
        plan.save(update_fields=["amount_paid", "status"])

        return success_response(
            message=f"EMI installment #{installment.month_number} paid. "
                    f"Remaining: ₹{plan.amount_remaining}"
        )


class AdminEMIOverviewView(APIView):
    """GET /api/v1/emi/admin/overview/"""
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        active   = EMIPlan.objects.filter(status=EMIPlan.Status.ACTIVE).count()
        defaulted = EMIPlan.objects.filter(status=EMIPlan.Status.DEFAULTED).count()
        overdue_installments = EMIInstallment.objects.filter(
            status=EMIInstallment.Status.OVERDUE
        ).count()

        return success_response(data={
            "active_plans":          active,
            "defaulted_plans":       defaulted,
            "overdue_installments":  overdue_installments,
        })