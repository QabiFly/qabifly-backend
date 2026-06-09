import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from core.responses import success_response, error_response
from apps.products.models import Product, ProductVariant
from .models import Cart, CartItem
from .serializers import (
    CartSerializer,
    AddToCartSerializer,
    UpdateCartItemSerializer,
)

logger = logging.getLogger("apps")


def get_or_create_cart(user):
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


class CartView(APIView):
    """GET /api/v1/cart/ — user ka cart dekho"""
    permission_classes = [IsAuthenticated]
    serializer_class = CartSerializer
    
    def get(self, request):
        cart = get_or_create_cart(request.user)
        serializer = CartSerializer(cart, context={"request": request})
        return success_response(data=serializer.data)


class AddToCartView(APIView):
    """
    POST /api/v1/cart/add/
    Rule: Sirf ek shop ka saman ek cart mein.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AddToCartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product_id = serializer.validated_data["product_id"]
        variant_id = serializer.validated_data.get("variant_id")
        quantity   = serializer.validated_data["quantity"]

        # Fetch product
        try:
            product = Product.objects.select_related("shop").get(
                id=product_id, status=Product.Status.ACTIVE
            )
        except Product.DoesNotExist:
            return error_response(message="Product not found.", status_code=404)

        # Stock check
        if product.stock < quantity:
            return error_response(
                message=f"Only {product.stock} units available.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # Variant check
        variant = None
        if variant_id:
            try:
                variant = ProductVariant.objects.get(
                    id=variant_id, product=product, is_active=True
                )
                if variant.stock < quantity:
                    return error_response(
                        message=f"Only {variant.stock} units of this variant available.",
                        status_code=status.HTTP_400_BAD_REQUEST,
                    )
            except ProductVariant.DoesNotExist:
                return error_response(message="Variant not found.", status_code=404)

        cart = get_or_create_cart(request.user)

        # Rule: single shop enforcement
        if cart.shop and cart.shop != product.shop:
            return error_response(
                message=(
                    f"Your cart has items from '{cart.shop.name}'. "
                    f"Clear cart to add items from '{product.shop.name}'."
                ),
                errors={"conflict": True, "current_shop": cart.shop.name,
                        "new_shop": product.shop.name},
                status_code=status.HTTP_409_CONFLICT,
            )

        # Set shop on cart
        if not cart.shop:
            cart.shop = product.shop
            cart.save(update_fields=["shop"])

        # Add or update cart item
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart, product=product, variant=variant,
            defaults={"quantity": quantity},
        )
        if not created:
            new_qty = cart_item.quantity + quantity
            if new_qty > product.stock:
                return error_response(
                    message=f"Cannot add more. Only {product.stock} units available.",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            cart_item.quantity = new_qty
            cart_item.save(update_fields=["quantity"])

        cart.refresh_from_db()
        return success_response(
            data=CartSerializer(cart, context={"request": request}).data,
            message="Item added to cart.",
            status_code=status.HTTP_201_CREATED,
        )


class UpdateCartItemView(APIView):
    """PATCH /api/v1/cart/items/<uuid:item_id>/"""
    permission_classes = [IsAuthenticated]

    def patch(self, request, item_id):
        try:
            item = CartItem.objects.select_related("product").get(
                id=item_id, cart__user=request.user
            )
        except CartItem.DoesNotExist:
            return error_response(message="Cart item not found.", status_code=404)

        serializer = UpdateCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_qty = serializer.validated_data["quantity"]

        if new_qty > item.product.stock:
            return error_response(
                message=f"Only {item.product.stock} units available.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        item.quantity = new_qty
        item.save(update_fields=["quantity"])
        cart = item.cart
        cart.refresh_from_db()
        return success_response(
            data=CartSerializer(cart, context={"request": request}).data,
            message="Cart updated.",
        )


class RemoveCartItemView(APIView):
    """DELETE /api/v1/cart/items/<uuid:item_id>/"""
    permission_classes = [IsAuthenticated]

    def delete(self, request, item_id):
        try:
            item = CartItem.objects.get(id=item_id, cart__user=request.user)
        except CartItem.DoesNotExist:
            return error_response(message="Cart item not found.", status_code=404)

        cart = item.cart
        item.delete()

        # If cart is empty, clear shop reference
        if not cart.items.exists():
            cart.shop = None
            cart.save(update_fields=["shop"])

        cart.refresh_from_db()
        return success_response(
            data=CartSerializer(cart, context={"request": request}).data,
            message="Item removed from cart.",
        )


class ClearCartView(APIView):
    """DELETE /api/v1/cart/clear/"""
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        cart = get_or_create_cart(request.user)
        cart.clear()
        return success_response(message="Cart cleared.")
