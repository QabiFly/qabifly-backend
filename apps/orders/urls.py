from django.urls import path
from .views import (
    PlaceOrderView,
    MyOrdersView,
    OrderDetailView,
    CancelOrderView,
    ShopOrdersView,
    UpdateOrderStatusView,
    VerifyDeliveryOTPView,
)

urlpatterns = [
    path("place/",                                  PlaceOrderView.as_view(),        name="order-place"),
    path("mine/",                                   MyOrdersView.as_view(),           name="my-orders"),
    path("shop/",                                   ShopOrdersView.as_view(),         name="shop-orders"),
    path("<str:order_number>/",                     OrderDetailView.as_view(),        name="order-detail"),
    path("<str:order_number>/cancel/",              CancelOrderView.as_view(),        name="order-cancel"),
    path("<str:order_number>/status/",              UpdateOrderStatusView.as_view(),  name="order-status"),
    path("<str:order_number>/verify-otp/",          VerifyDeliveryOTPView.as_view(),  name="order-verify-otp"),
]