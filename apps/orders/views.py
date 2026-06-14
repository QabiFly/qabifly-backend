import logging
from django.utils import timezone
from django.db import transaction
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from core.responses import success_response, error_response
from core.permissions import IsShopkeeper, IsDeliveryBoy, IsAdminUser, IsBuyerOrAdmin
from apps.cart.models import Cart
from .models import Order, OrderItem, OrderStatusLog
from .serializers import (
    PlaceOrderSerializer,
    OrderListSerializer,
    OrderDetailSerializer,
    CancelOrderSerializer,
    UpdateOrderStatusSerializer,
    VerifyDeliveryOTPSerializer,
)
from .utils import generate_order_number, generate_delivery_otp

logger = logging.getLogger("apps")


def log_status_change(order, from_status, to_status, changed_by=None, note=""):
    OrderStatusLog.objects.create(
        order=order,
        from_status=from_status,
        to_status=to_status,
        changed_by=changed_by,
        note=note,
    )


# ── Place Order ───────────────────────────────────────────────────────────────

class PlaceOrderView(APIView):
    """
    POST /api/v1/orders/place/
    Rules:
    - User must be email verified
    - Cart must not be empty
    - All items must be in stock
    - Stock deducted atomically on order creation
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        if not request.user.is_verified:
            return error_response(
                message="Please verify your email before placing an order.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        serializer = PlaceOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Get cart
        try:
            cart = Cart.objects.prefetch_related(
                "items__product", "items__variant"
            ).get(user=request.user)
        except Cart.DoesNotExist:
            return error_response(message="Your cart is empty.", status_code=400)

        if not cart.items.exists():
            return error_response(message="Your cart is empty.", status_code=400)

        if not cart.shop:
            return error_response(message="Cart has no shop assigned.", status_code=400)

        shop = cart.shop
        if not shop.can_accept_orders:
            return error_response(
                message=f"'{shop.name}' is currently not accepting orders.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # Stock validation for all items before any deduction
        for item in cart.items.all():
            available = item.variant.stock if item.variant else item.product.stock
            if item.quantity > available:
                return error_response(
                    message=f"'{item.product.name}' has only {available} units in stock.",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

        # Coupon validation (basic — full coupon block in Block 5)
        discount_amount = 0
        coupon_code = data.get("coupon_code", "")
        if coupon_code:
            from apps.coupons.models import Coupon
            try:
                coupon = Coupon.objects.get(
                    code=coupon_code, is_active=True, shop=shop
                )
                discount_amount = coupon.calculate_discount(cart.subtotal)
            except Exception:
                return error_response(
                    message=f"Coupon '{coupon_code}' is invalid or expired.",
                    status_code=400,
                )

        subtotal        = cart.subtotal
        delivery_charge = 0
        total_amount    = max(0, subtotal + delivery_charge - discount_amount)

        # Udhaar limit check
        if data["payment_method"] == "UDHAAR":
            from apps.udhaar.models import UdhaarRecord
            from django.conf import settings as django_settings
            current_udhaar = UdhaarRecord.objects.filter(
                buyer=request.user, shop=shop, is_settled=False
            ).aggregate(total=__import__("django.db.models", fromlist=["Sum"]).Sum("amount"))["total"] or 0
            max_limit = django_settings.MAX_UDHAAR_LIMIT
            if current_udhaar + total_amount > max_limit:
                return error_response(
                    message=f"Udhaar limit exceeded. Current: ₹{current_udhaar}, Limit: ₹{max_limit}",
                    status_code=400,
                )

        # Wallet balance check
        if data["payment_method"] == "WALLET":
            from apps.wallet.models import Wallet
            wallet, _ = Wallet.objects.get_or_create(user=request.user)
            if wallet.balance < total_amount:
                return error_response(
                    message=f"Insufficient wallet balance. Available: ₹{wallet.balance}",
                    status_code=400,
                )

        # Create order
        order = Order.objects.create(
            order_number       = generate_order_number(),
            buyer              = request.user,
            shop               = shop,
            status             = Order.Status.PENDING,
            payment_method     = data["payment_method"],
            payment_status     = "PAID" if data["payment_method"] == "COD" else "PENDING",
            subtotal           = subtotal,
            delivery_charge    = delivery_charge,
            discount_amount    = discount_amount,
            total_amount       = total_amount,
            delivery_address   = data["delivery_address"],
            delivery_lat       = data.get("delivery_lat"),
            delivery_lon       = data.get("delivery_lon"),
            delivery_otp       = generate_delivery_otp(),
            coupon_code        = coupon_code,
            buyer_note         = data.get("buyer_note", ""),
        )

        # Create order items + deduct stock
        for item in cart.items.all():
            OrderItem.objects.create(
                order        = order,
                product      = item.product,
                variant      = item.variant,
                product_name = item.product.name,
                variant_name = item.variant.name if item.variant else "",
                unit_price   = item.unit_price,
                quantity     = item.quantity,
                line_total   = item.line_total,
            )
            # Deduct stock atomically
            if item.variant:
                item.variant.stock -= item.quantity
                item.variant.save(update_fields=["stock"])
            else:
                item.product.deduct_stock(item.quantity)

        # Wallet deduction
        if data["payment_method"] == "WALLET":
            wallet.balance -= total_amount
            wallet.save(update_fields=["balance"])
            order.payment_status = "PAID"
            order.save(update_fields=["payment_status"])

        # Udhaar record
        if data["payment_method"] == "UDHAAR":
            from apps.udhaar.models import UdhaarRecord
            from datetime import timedelta
            UdhaarRecord.objects.create(
                buyer    = request.user,
                shop     = shop,
                order    = order,
                amount   = total_amount,
                due_date = timezone.now().date() + timedelta(days=30),
            )

        # Log initial status
        log_status_change(order, "", Order.Status.PENDING, request.user, "Order placed")

        # Clear cart
        cart.clear()

        # Shop stats update
        shop.total_orders += 1
        shop.save(update_fields=["total_orders"])
# ── WhatsApp Trigger ──────────────────────────────────────
        # Shopkeeper ko WhatsApp pe order alert bhejo
        try:
            from celery_app.tasks.notification_tasks import notify_shopkeeper_whatsapp
            notify_shopkeeper_whatsapp.delay(str(order.id))
        except Exception as e:
            logger.warning(f"WhatsApp notify failed (non-critical): {e}")
        # ─────────────────────────────────────────────────────────
        
        logger.info(f"Order placed: #{order.order_number} by {request.user.email}")
        return success_response(
            data=OrderDetailSerializer(order).data,
            message="Order placed successfully.",
            status_code=status.HTTP_201_CREATED,
        )


# ── Buyer — My Orders ─────────────────────────────────────────────────────────

class MyOrdersView(generics.ListAPIView):
    """GET /api/v1/orders/mine/"""
    permission_classes = [IsAuthenticated]
    serializer_class   = OrderListSerializer

    def get_queryset(self):
        return Order.objects.filter(buyer=self.request.user).select_related("shop")

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return success_response(data=serializer.data)


class OrderDetailView(APIView):
    """GET /api/v1/orders/<order_number>/"""
    permission_classes = [IsAuthenticated]

    def get(self, request, order_number):
        try:
            order = Order.objects.prefetch_related(
                "items", "status_logs"
            ).select_related("shop", "buyer").get(order_number=order_number)
        except Order.DoesNotExist:
            return error_response(message="Order not found.", status_code=404)

        # Only buyer, shopkeeper of that shop, or admin can view
        user = request.user
        if not (
            order.buyer == user
            or (hasattr(user, "shop") and user.shop == order.shop)
            or user.role == "ADMIN"
        ):
            return error_response(
                message="You do not have permission to view this order.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        return success_response(data=OrderDetailSerializer(order).data)


class CancelOrderView(APIView):
    """POST /api/v1/orders/<order_number>/cancel/"""
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, order_number):
        try:
            order = Order.objects.get(order_number=order_number, buyer=request.user)
        except Order.DoesNotExist:
            return error_response(message="Order not found.", status_code=404)

        if not order.can_cancel:
            return error_response(
                message=f"Order cannot be cancelled in '{order.status}' state.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        serializer = CancelOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        prev_status = order.status
        order.status = Order.Status.CANCELLED
        order.cancellation_reason = serializer.validated_data["reason"]
        order.cancelled_at = timezone.now()
        order.save(update_fields=["status", "cancellation_reason", "cancelled_at"])

        # Restore stock
        for item in order.items.all():
            if item.variant:
                item.variant.stock += item.quantity
                item.variant.save(update_fields=["stock"])
            else:
                item.product.restore_stock(item.quantity)

        # Refund wallet if paid via wallet
        if order.payment_method == "WALLET" and order.payment_status == "PAID":
            from apps.wallet.models import Wallet
            wallet, _ = Wallet.objects.get_or_create(user=request.user)
            wallet.balance += order.total_amount
            wallet.save(update_fields=["balance"])
            order.payment_status = "REFUNDED"
            order.save(update_fields=["payment_status"])

        log_status_change(order, prev_status, Order.Status.CANCELLED, request.user,
                          serializer.validated_data["reason"])

        return success_response(message="Order cancelled successfully.")


# ── Shopkeeper — Order Management ─────────────────────────────────────────────

class ShopOrdersView(generics.ListAPIView):
    """GET /api/v1/orders/shop/?status=PENDING"""
    permission_classes = [IsAuthenticated, IsShopkeeper]
    serializer_class   = OrderListSerializer

    def get_queryset(self):
        qs = Order.objects.filter(
            shop=self.request.user.shop
        ).select_related("buyer")
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter.upper())
        return qs

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return success_response(data=serializer.data)


class UpdateOrderStatusView(APIView):
    """
    POST /api/v1/orders/<order_number>/status/
    Shopkeeper status update karta hai.
    Allowed transitions:
    PENDING → CONFIRMED → PREPARING → READY
    READY → PICKED (delivery boy karta hai)
    PICKED → DELIVERED (delivery boy OTP verify karta hai)
    """
    permission_classes = [IsAuthenticated, IsShopkeeper]

    ALLOWED_TRANSITIONS = {
        "PENDING":   ["CONFIRMED", "CANCELLED"],
        "CONFIRMED": ["PREPARING", "CANCELLED"],
        "PREPARING": ["READY"],
        "READY":     [],  # delivery boy ke liye
    }

    def post(self, request, order_number):
        try:
            order = Order.objects.get(
                order_number=order_number, shop=request.user.shop
            )
        except Order.DoesNotExist:
            return error_response(message="Order not found.", status_code=404)

        serializer = UpdateOrderStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data["status"]

        allowed = self.ALLOWED_TRANSITIONS.get(order.status, [])
        if new_status not in allowed:
            return error_response(
                message=f"Cannot move order from '{order.status}' to '{new_status}'.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        prev_status = order.status
        order.status = new_status
        if new_status == "CONFIRMED":
    order.confirmed_at = timezone.now()
    order.payment_status = "PAID" if order.payment_method == "COD" else order.payment_status

order.save(update_fields=["status", "confirmed_at", "payment_status"])

# Jab status CONFIRMED hota hai, delivery boys ko notify karo
if new_status == "CONFIRMED":
order.confirmed_at = timezone.now()
order.payment_status = (
"PAID" if order.payment_method == "COD"
else order.payment_status
)

# Delivery boys notification
try:
    from apps.orders.tasks import notify_delivery_boys_new_order
    notify_delivery_boys_new_order.delay(str(order.id))
except Exception as e:
    logger.warning(f"Delivery boys notification failed: {e}")

order.save(update_fields=["status", "confirmed_at", "payment_status"])

log_status_change(
order,
prev_status,
new_status,
request.user,
serializer.validated_data.get("note", "")
)

return success_response(
message=f"Order status updated to '{new_status}'."
)
# ── Delivery Boy ──────────────────────────────────────────────────────────────

class VerifyDeliveryOTPView(APIView):
    """
    POST /api/v1/orders/<order_number>/verify-otp/
    Delivery boy buyer se OTP leta hai, verify karta hai → DELIVERED.
    """
    permission_classes = [IsAuthenticated, IsDeliveryBoy]

    @transaction.atomic
    def post(self, request, order_number):
        try:
            order = Order.objects.get(
                order_number=order_number, status=Order.Status.PICKED
            )
        except Order.DoesNotExist:
            return error_response(message="Order not found or not in PICKED state.", status_code=404)

        serializer = VerifyDeliveryOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if order.delivery_otp != serializer.validated_data["otp_code"]:
            return error_response(
                message="Incorrect delivery OTP.", status_code=status.HTTP_400_BAD_REQUEST
            )

        prev_status = order.status
        order.status = Order.Status.DELIVERED
        order.delivery_otp_verified = True
        order.delivered_at = timezone.now()
        order.save(update_fields=["status", "delivery_otp_verified", "delivered_at"])

        # Payment split — trigger in background
        from celery_app.tasks.notification_tasks import trigger_payment_split
        trigger_payment_split.delay(str(order.id))

        log_status_change(order, prev_status, Order.Status.DELIVERED, request.user,
                          "Delivery OTP verified")

        return success_response(message="Order delivered successfully.")
