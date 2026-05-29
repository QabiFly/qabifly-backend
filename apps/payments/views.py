import logging
from django.utils import timezone
from django.db import transaction
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from core.responses import success_response, error_response
from core.permissions import IsAdminUser
from apps.orders.models import Order
from .models import Payment, PaymentSplit
from .serializers import (
    PaymentSerializer,
    SubmitUTRSerializer,
    AdminVerifyPaymentSerializer,
    PaymentSplitSerializer,
)
from .utils import generate_upi_deep_link

logger = logging.getLogger("apps")


class GetUPIDeepLinkView(APIView):
    """
    GET /api/v1/payments/upi/<order_number>/
    Returns UPI deep link — Flutter will launch this to open UPI apps.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, order_number):
        try:
            order = Order.objects.get(
                order_number=order_number, buyer=request.user
            )
        except Order.DoesNotExist:
            return error_response(message="Order not found.", status_code=404)

        if order.payment_method != Order.PaymentMethod.UPI:
            return error_response(
                message="This order does not use UPI payment.",
                status_code=400,
            )

        if order.payment_status == "PAID":
            return error_response(message="This order is already paid.", status_code=400)

        deep_link_data = generate_upi_deep_link(
            amount=float(order.total_amount),
            order_number=order.order_number,
        )

        # Create or update payment record
        payment, _ = Payment.objects.get_or_create(
            order=order,
            defaults={
                "method": Payment.Method.UPI,
                "amount": order.total_amount,
                "upi_id": deep_link_data["upi_id"],
                "upi_deep_link": deep_link_data["upi_link"],
            }
        )

        return success_response(data=deep_link_data)


class SubmitUTRView(APIView):
    """
    POST /api/v1/payments/upi/submit-utr/
    User pays via UPI app, then submits UTR number for admin verification.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SubmitUTRSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            order = Order.objects.get(
                order_number=serializer.validated_data["order_number"],
                buyer=request.user,
                payment_method=Order.PaymentMethod.UPI,
            )
        except Order.DoesNotExist:
            return error_response(message="Order not found.", status_code=404)

        if order.payment_status == "PAID":
            return error_response(message="Payment already verified.", status_code=400)

        payment, _ = Payment.objects.get_or_create(
            order=order,
            defaults={"method": Payment.Method.UPI, "amount": order.total_amount}
        )
        payment.utr_number = serializer.validated_data["utr_number"]
        payment.save(update_fields=["utr_number"])

        logger.info(f"UTR submitted for order #{order.order_number}: {payment.utr_number}")
        return success_response(
            message="UTR submitted. Admin will verify your payment shortly."
        )


class AdminVerifyPaymentView(APIView):
    """
    POST /api/v1/payments/admin/<order_number>/verify/
    Admin manually verifies or rejects UPI payment.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    @transaction.atomic
    def post(self, request, order_number):
        try:
            order = Order.objects.get(order_number=order_number)
            payment = order.payment
        except (Order.DoesNotExist, Payment.DoesNotExist):
            return error_response(message="Order or payment not found.", status_code=404)

        serializer = AdminVerifyPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        action = serializer.validated_data["action"]

        if action == "verify":
            payment.status      = Payment.Status.PAID
            payment.verified_by = request.user
            payment.verified_at = timezone.now()
            payment.save(update_fields=["status", "verified_by", "verified_at"])

            order.payment_status = "PAID"
            order.save(update_fields=["payment_status"])

            logger.info(f"Payment verified for order #{order_number} by {request.user.email}")
            return success_response(message=f"Payment for order #{order_number} verified.")
        else:
            payment.status         = Payment.Status.FAILED
            payment.failure_reason = serializer.validated_data.get("failure_reason", "")
            payment.save(update_fields=["status", "failure_reason"])

            order.payment_status = "FAILED"
            order.save(update_fields=["payment_status"])

            return success_response(message=f"Payment for order #{order_number} rejected.")


class MyPaymentsView(APIView):
    """GET /api/v1/payments/mine/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        payments = Payment.objects.filter(
            order__buyer=request.user
        ).select_related("order")
        serializer = PaymentSerializer(payments, many=True)
        return success_response(data=serializer.data)


class AdminPendingPaymentsView(APIView):
    """GET /api/v1/payments/admin/pending/ — UTR submitted, awaiting verification"""
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        payments = Payment.objects.filter(
            method=Payment.Method.UPI,
            status=Payment.Status.PENDING,
        ).exclude(utr_number="").select_related("order__buyer")
        serializer = PaymentSerializer(payments, many=True)
        return success_response(data=serializer.data)