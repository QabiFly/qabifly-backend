from django.urls import path
from .views import (
    ShopCategoryListView,
    NearbyShopsView,
    MyShopView,
    CreateShopView,
    UpdateShopView,
    ToggleShopOpenView,
    UploadShopDocumentView,
    ShopDetailView,
    AdminShopListView,
    AdminApproveShopView,
)

urlpatterns = [
    # Public
    path("categories/",                    ShopCategoryListView.as_view(),   name="shop-categories"),
    path("nearby/",                        NearbyShopsView.as_view(),        name="shops-nearby"),
    path("<slug:slug>/",                   ShopDetailView.as_view(),         name="shop-detail"),

    # Shopkeeper
    path("mine/",                          MyShopView.as_view(),             name="my-shop"),
    path("create/",                        CreateShopView.as_view(),         name="shop-create"),
    path("mine/update/",                   UpdateShopView.as_view(),         name="shop-update"),
    path("mine/toggle-open/",             ToggleShopOpenView.as_view(),     name="shop-toggle-open"),
    path("mine/documents/",               UploadShopDocumentView.as_view(), name="shop-documents"),

    # Admin
    path("admin/list/",                    AdminShopListView.as_view(),      name="admin-shop-list"),
    path("admin/<uuid:shop_id>/approve/",  AdminApproveShopView.as_view(),   name="admin-shop-approve"),
]