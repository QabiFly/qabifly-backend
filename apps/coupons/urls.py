from django.urls import path
from .views import (
    ValidateCouponView,
    PublicCouponsView,
    ShopCouponsView,
    AdminCreateCouponView,
    AdminCouponListView,
    AdminToggleCouponView,
    AdminCouponUsageView,
)

urlpatterns = [
    path("",                                    PublicCouponsView.as_view(),       name="coupons-public"),
    path("validate/",                           ValidateCouponView.as_view(),      name="coupon-validate"),
    path("shop/<uuid:shop_id>/",                ShopCouponsView.as_view(),         name="shop-coupons"),
    path("admin/create/",                       AdminCreateCouponView.as_view(),   name="admin-coupon-create"),
    path("admin/list/",                         AdminCouponListView.as_view(),     name="admin-coupon-list"),
    path("admin/<uuid:coupon_id>/toggle/",      AdminToggleCouponView.as_view(),   name="admin-coupon-toggle"),
    path("admin/<uuid:coupon_id>/usage/",       AdminCouponUsageView.as_view(),    name="admin-coupon-usage"),
]