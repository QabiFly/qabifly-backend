import logging
from django.utils import timezone
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny

from core.responses import success_response, error_response
from core.permissions import IsShopkeeper, IsAdminUser
from .models import Shop, ShopCategory, ShopDocument
from .serializers import (
    ShopCategorySerializer,
    ShopCreateSerializer,
    ShopPublicSerializer,
    ShopOwnerSerializer,
    ShopUpdateSerializer,
    ShopAdminSerializer,
    ShopApproveSerializer,
    ShopDocumentSerializer,
)
from .utils import haversine_distance_km

logger = logging.getLogger("apps")

DELIVERY_RADIUS_KM = 2


# ── Categories ────────────────────────────────────────────────────────────────

class ShopCategoryListView(generics.ListAPIView):
    """GET /api/v1/shops/categories/ — public"""
    permission_classes = [AllowAny]
    serializer_class   = ShopCategorySerializer
    queryset = ShopCategory.objects.filter(is_active=True)


# ── Nearby Shops (Buyer) ──────────────────────────────────────────────────────

class NearbyShopsView(APIView):
    """
    GET /api/v1/shops/nearby/?lat=25.xx&lon=83.xx
    Returns shops within 2km radius. Public endpoint.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            buyer_lat = float(request.query_params.get("lat"))
            buyer_lon = float(request.query_params.get("lon"))
        except (TypeError, ValueError):
            return error_response(
                message="lat and lon query params are required (e.g. ?lat=25.12&lon=83.45)",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        active_shops = Shop.objects.filter(
            status=Shop.Status.ACTIVE,
            is_open=True,
            latitude__isnull=False,
            longitude__isnull=False,
        ).select_related("category", "owner")

        nearby = []
        for shop in active_shops:
            dist = haversine_distance_km(
                buyer_lat, buyer_lon,
                float(shop.latitude), float(shop.longitude),
            )
            if dist <= DELIVERY_RADIUS_KM:
                data = ShopPublicSerializer(shop).data
                data["distance_km"] = round(dist, 2)
                nearby.append(data)

        nearby.sort(key=lambda x: x["distance_km"])
        return success_response(data=nearby)


# ── Shopkeeper — Own Shop ─────────────────────────────────────────────────────

class MyShopView(APIView):
    """GET /api/v1/shops/mine/ — shopkeeper apni shop dekhe"""
    permission_classes = [IsAuthenticated, IsShopkeeper]

    def get(self, request):
        try:
            shop = request.user.shop
        except Shop.DoesNotExist:
            return error_response(
                message="You have not registered a shop yet.",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return success_response(data=ShopOwnerSerializer(shop).data)


class CreateShopView(APIView):
    """POST /api/v1/shops/create/ — shopkeeper registers a shop"""
    permission_classes = [IsAuthenticated, IsShopkeeper]

    def post(self, request):
        serializer = ShopCreateSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        shop = serializer.save()
        logger.info(f"New shop registered: {shop.name} by {request.user.email}")
        return success_response(
            data=ShopOwnerSerializer(shop).data,
            message="Shop registered successfully. Pending admin approval.",
            status_code=status.HTTP_201_CREATED,
        )


class UpdateShopView(APIView):
    """PATCH /api/v1/shops/mine/update/"""
    permission_classes = [IsAuthenticated, IsShopkeeper]

    def patch(self, request):
        try:
            shop = request.user.shop
        except Shop.DoesNotExist:
            return error_response(
                message="Shop not found.", status_code=status.HTTP_404_NOT_FOUND
            )
        serializer = ShopUpdateSerializer(shop, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(
            data=ShopOwnerSerializer(shop).data,
            message="Shop updated successfully.",
        )


class ToggleShopOpenView(APIView):
    """POST /api/v1/shops/mine/toggle-open/ — open/close shop"""
    permission_classes = [IsAuthenticated, IsShopkeeper]

    def post(self, request):
        try:
            shop = request.user.shop
        except Shop.DoesNotExist:
            return error_response(message="Shop not found.", status_code=404)

        if shop.status != Shop.Status.ACTIVE:
            return error_response(
                message="Only approved shops can be opened or closed.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        shop.is_open = not shop.is_open
        shop.save(update_fields=["is_open"])
        state = "opened" if shop.is_open else "closed"
        return success_response(message=f"Shop {state} successfully.")


class UploadShopDocumentView(APIView):
    """POST /api/v1/shops/mine/documents/ — upload verification docs"""
    permission_classes = [IsAuthenticated, IsShopkeeper]

    def post(self, request):
        try:
            shop = request.user.shop
        except Shop.DoesNotExist:
            return error_response(message="Shop not found.", status_code=404)

        serializer = ShopDocumentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(shop=shop)
        return success_response(
            data=serializer.data,
            message="Document uploaded successfully.",
            status_code=status.HTTP_201_CREATED,
        )


# ── Public Shop Detail ────────────────────────────────────────────────────────

class ShopDetailView(APIView):
    """GET /api/v1/shops/<slug>/ — public shop detail"""
    permission_classes = [AllowAny]

    def get(self, request, slug):
        try:
            shop = Shop.objects.select_related(
                "category", "owner"
            ).get(slug=slug, status=Shop.Status.ACTIVE)
        except Shop.DoesNotExist:
            return error_response(
                message="Shop not found.", status_code=status.HTTP_404_NOT_FOUND
            )
        return success_response(data=ShopPublicSerializer(shop).data)


# ── Admin ─────────────────────────────────────────────────────────────────────

class AdminShopListView(generics.ListAPIView):
    """GET /api/v1/shops/admin/list/?status=PENDING"""
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class   = ShopAdminSerializer

    def get_queryset(self):
        qs     = Shop.objects.select_related("category", "owner", "approved_by")
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter.upper())
        return qs

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data)


class AdminApproveShopView(APIView):
    """POST /api/v1/shops/admin/<shop_id>/approve/"""
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, shop_id):
        try:
            shop = Shop.objects.get(id=shop_id)
        except Shop.DoesNotExist:
            return error_response(message="Shop not found.", status_code=404)

        serializer = ShopApproveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        action = serializer.validated_data["action"]

        if action == "approve":
            shop.status      = Shop.Status.ACTIVE
            shop.approved_by = request.user
            shop.approved_at = timezone.now()
            shop.rejection_reason = ""
            shop.save(update_fields=["status", "approved_by", "approved_at", "rejection_reason"])
            logger.info(f"Shop approved: {shop.name} by admin {request.user.email}")
            return success_response(message=f"Shop '{shop.name}' approved successfully.")
        else:
            shop.status = Shop.Status.REJECTED
            shop.rejection_reason = serializer.validated_data["rejection_reason"]
            shop.save(update_fields=["status", "rejection_reason"])
            logger.info(f"Shop rejected: {shop.name} — reason: {shop.rejection_reason}")
            return success_response(message=f"Shop '{shop.name}' rejected.")