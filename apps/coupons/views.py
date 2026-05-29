import logging
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny

from core.responses import success_response, error_response
from core.permissions import IsAdminUser
from apps.orders.models import Order
from .models import Coupon, CouponUsage
from .serializers import (
    CouponSerializer,
    CreateCouponSerializer,
    ValidateCouponSerializer,
    CouponUsageSerializer,
)

logger = logging.getLogger("apps")


class ValidateCouponView(APIView):
    """
    POST /api/v1/coupons/validate/
    Cart mein coupon apply karne se pehle validate karo.
    Returns discount amount if valid.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ValidateCouponSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            coupon = Coupon.objects.get(code=data["code"].upper())
        except Coupon.DoesNotExist:
            return error_response(message="Invalid coupon code.", status_code=400)

        if not coupon.is_valid_now:
            return error_response(message="This coupon is expired or no longer valid.", status_code=400)

        # Shop-specific coupon check
        if coupon.shop and data.get("shop_id"):
            if str(coupon.shop.id) != str(data["shop_id"]):
                return error_response(
                    message="This coupon is not valid for this shop.", status_code=400
                )

        # Min order check
        if float(data["order_amount"]) < float(coupon.min_order_amount):
            return error_response(
                message=f"Minimum order of ₹{coupon.min_order_amount} required for this coupon.",
                status_code=400,
            )

        # Per user usage check
        user_usage = CouponUsage.objects.filter(coupon=coupon, user=request.user).count()
        if user_usage >= coupon.max_uses_per_user:
            return error_response(
                message="You have already used this coupon the maximum number of times.",
                status_code=400,
            )

        # First order check
        if coupon.discount_type == Coupon.DiscountType.FIRST_ORDER:
            has_orders = Order.objects.filter(
                buyer=request.user, status=Order.Status.DELIVERED
            ).exists()
            if has_orders:
                return error_response(
                    message="This coupon is only for first-time orders.", status_code=400
                )

        discount = coupon.calculate_discount(float(data["order_amount"]))

        return success_response(data={
            "code":            coupon.code,
            "discount_type":   coupon.discount_type,
            "discount_value":  float(coupon.discount_value),
            "discount_amount": discount,
            "description":     coupon.description,
        })


class PublicCouponsView(generics.ListAPIView):
    """GET /api/v1/coupons/ — active platform-wide coupons"""
    permission_classes = [AllowAny]
    serializer_class   = CouponSerializer

    def get_queryset(self):
        return Coupon.objects.filter(is_active=True, shop__isnull=True)

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return success_response(data=serializer.data)


class ShopCouponsView(generics.ListAPIView):
    """GET /api/v1/coupons/shop/<uuid:shop_id>/"""
    permission_classes = [AllowAny]
    serializer_class   = CouponSerializer

    def get_queryset(self):
        return Coupon.objects.filter(
            shop_id=self.kwargs["shop_id"], is_active=True
        )

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return success_response(data=serializer.data)


# ── Admin ─────────────────────────────────────────────────────────────────────

class AdminCreateCouponView(APIView):
    """POST /api/v1/coupons/admin/create/"""
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        serializer = CreateCouponSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        coupon = serializer.save(created_by=request.user)
        logger.info(f"Coupon created: {coupon.code} by {request.user.email}")
        return success_response(
            data=CouponSerializer(coupon).data,
            message=f"Coupon '{coupon.code}' created successfully.",
            status_code=status.HTTP_201_CREATED,
        )


class AdminCouponListView(generics.ListAPIView):
    """GET /api/v1/coupons/admin/list/"""
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class   = CouponSerializer

    def get_queryset(self):
        qs = Coupon.objects.select_related("shop", "created_by")
        active = self.request.query_params.get("active")
        if active is not None:
            qs = qs.filter(is_active=active.lower() == "true")
        return qs

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return success_response(data=serializer.data)


class AdminToggleCouponView(APIView):
    """POST /api/v1/coupons/admin/<uuid:coupon_id>/toggle/"""
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, coupon_id):
        try:
            coupon = Coupon.objects.get(id=coupon_id)
        except Coupon.DoesNotExist:
            return error_response(message="Coupon not found.", status_code=404)
        coupon.is_active = not coupon.is_active
        coupon.save(update_fields=["is_active"])
        state = "activated" if coupon.is_active else "deactivated"
        return success_response(message=f"Coupon '{coupon.code}' {state}.")


class AdminCouponUsageView(generics.ListAPIView):
    """GET /api/v1/coupons/admin/<uuid:coupon_id>/usage/"""
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class   = CouponUsageSerializer

    def get_queryset(self):
        return CouponUsage.objects.filter(
            coupon_id=self.kwargs["coupon_id"]
        ).select_related("user", "order", "coupon")

    def list(self, request, *args, **kwargs):
        queryset   = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        total_discount = sum(u.discount_applied for u in queryset)
        return success_response(data={
            "total_uses":     queryset.count(),
            "total_discount": float(total_discount),
            "usages":         serializer.data,
        })