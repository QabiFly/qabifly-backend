import logging
import uuid

from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated

from core.responses import success_response, error_response
from core.permissions import IsShopkeeper
from .models import Product, ProductCategory, ProductImage, ProductVariant, ProductReview
from .serializers import (
    ProductCategorySerializer,
    ProductCreateSerializer,
    ProductListSerializer,
    ProductDetailSerializer,
    ProductUpdateSerializer,
    ProductImageSerializer,
    ProductVariantSerializer,
    ProductReviewSerializer,
)

logger = logging.getLogger("apps")


class ProductCategoryListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = ProductCategorySerializer
    queryset = ProductCategory.objects.filter(is_active=True, parent__isnull=True)


class ProductListView(generics.ListAPIView):
    serializer_class = ProductListSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = Product.objects.filter(
            status=Product.Status.ACTIVE
        ).select_related(
            "category", "shop"
        ).prefetch_related("images")

        search = self.request.query_params.get("search")
        if search:
            vector = SearchVector("name", "description")
            query = SearchQuery(search)
            qs = qs.annotate(
                rank=SearchRank(vector, query)
            ).filter(rank__gte=0.001).order_by("-rank")

        shop_slug = self.request.query_params.get("shop")
        if shop_slug:
            try:
                uuid.UUID(shop_slug)
                qs = qs.filter(shop_id=shop_slug)
            except ValueError:
                qs = qs.filter(shop__slug=shop_slug)

        category_slug = self.request.query_params.get("category")
        featured = self.request.query_params.get("featured")
        min_price = self.request.query_params.get("min_price")
        max_price = self.request.query_params.get("max_price")

        if category_slug:
            qs = qs.filter(category__slug=category_slug)
        if featured == "true":
            qs = qs.filter(is_featured=True)
        if min_price:
            qs = qs.filter(price__gte=min_price)
        if max_price:
            qs = qs.filter(price__lte=max_price)

        return qs

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(
            queryset, many=True, context={"request": request}
        )
        return success_response(data=serializer.data)


class ProductDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, slug):
        try:
            product = Product.objects.select_related(
                "category", "shop"
            ).prefetch_related(
                "images", "variants", "reviews__user"
            ).get(slug=slug)
        except Product.DoesNotExist:
            return error_response(message="Product not found.", status_code=404)

        return success_response(
            data=ProductDetailSerializer(
                product, context={"request": request}
            ).data
        )


class MyProductsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsShopkeeper]
    serializer_class = ProductListSerializer

    def get_queryset(self):
        return Product.objects.filter(
            shop=self.request.user.shop
        ).exclude(
            status=Product.Status.DELETED
        ).select_related("category").prefetch_related("images")

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(
            queryset, many=True, context={"request": request}
        )
        return success_response(data=serializer.data)


class CreateProductView(APIView):
    permission_classes = [IsAuthenticated, IsShopkeeper]

    def post(self, request):
        serializer = ProductCreateSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        product = serializer.save()

        logger.info(f"Product created: {product.name} in shop {product.shop.name}")

        return success_response(
            data=ProductDetailSerializer(
                product, context={"request": request}
            ).data,
            message="Product created successfully.",
            status_code=status.HTTP_201_CREATED,
        )


class UpdateProductView(APIView):
    permission_classes = [IsAuthenticated, IsShopkeeper]

    def patch(self, request, product_id):
        try:
            product = Product.objects.get(id=product_id, shop=request.user.shop)
        except Product.DoesNotExist:
            return error_response(message="Product not found.", status_code=404)

        serializer = ProductUpdateSerializer(product, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return success_response(
            data=ProductDetailSerializer(
                product, context={"request": request}
            ).data,
            message="Product updated.",
        )


class DeleteProductView(APIView):
    permission_classes = [IsAuthenticated, IsShopkeeper]

    def delete(self, request, product_id):
        try:
            product = Product.objects.get(id=product_id, shop=request.user.shop)
        except Product.DoesNotExist:
            return error_response(message="Product not found.", status_code=404)

        product.status = Product.Status.DELETED
        product.save(update_fields=["status"])

        return success_response(message="Product deleted.")


class UploadProductImageView(APIView):
    permission_classes = [IsAuthenticated, IsShopkeeper]

    def post(self, request, product_id):
        try:
            product = Product.objects.get(id=product_id, shop=request.user.shop)
        except Product.DoesNotExist:
            return error_response(message="Product not found.", status_code=404)

        serializer = ProductImageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(product=product)

        return success_response(
            data=serializer.data,
            message="Image uploaded.",
            status_code=status.HTTP_201_CREATED,
        )


class AddProductVariantView(APIView):
    permission_classes = [IsAuthenticated, IsShopkeeper]

    def post(self, request, product_id):
        try:
            product = Product.objects.get(id=product_id, shop=request.user.shop)
        except Product.DoesNotExist:
            return error_response(message="Product not found.", status_code=404)

        serializer = ProductVariantSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(product=product)

        return success_response(
            data=serializer.data,
            message="Variant added.",
            status_code=status.HTTP_201_CREATED,
        )


class AddReviewView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, product_id):
        try:
            product = Product.objects.get(
                id=product_id,
                status=Product.Status.ACTIVE,
            )
        except Product.DoesNotExist:
            return error_response(message="Product not found.", status_code=404)

        from apps.orders.models import Order

        has_ordered = Order.objects.filter(
            buyer=request.user,
            shop=product.shop,
            status=Order.Status.DELIVERED,
        ).exists()

        if not has_ordered:
            return error_response(
                message="You can only review products from shops you have ordered from.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        if ProductReview.objects.filter(product=product, user=request.user).exists():
            return error_response(
                message="You have already reviewed this product.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        serializer = ProductReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        review = serializer.save(product=product, user=request.user)

        reviews = product.reviews.filter(is_visible=True)
        count = reviews.count()

        if count > 0:
            avg_rating = sum(r.rating for r in reviews) / count
            product.average_rating = round(avg_rating, 2)
            product.total_reviews = count
            product.save(update_fields=["average_rating", "total_reviews"])

        return success_response(
            data=ProductReviewSerializer(review).data,
            message="Review submitted.",
            status_code=status.HTTP_201_CREATED,
        )
