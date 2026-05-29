from django.urls import path
from .views import (
    ProductCategoryListView,
    ProductListView,
    ProductDetailView,
    MyProductsView,
    CreateProductView,
    UpdateProductView,
    DeleteProductView,
    UploadProductImageView,
    AddProductVariantView,
    AddReviewView,
)

urlpatterns = [
    # Public
    path("categories/",                                 ProductCategoryListView.as_view(),  name="product-categories"),
    path("",                                            ProductListView.as_view(),           name="product-list"),
    path("<slug:slug>/",                                ProductDetailView.as_view(),         name="product-detail"),

    # Shopkeeper
    path("mine/",                                       MyProductsView.as_view(),            name="my-products"),
    path("create/",                                     CreateProductView.as_view(),         name="product-create"),
    path("<uuid:product_id>/update/",                   UpdateProductView.as_view(),         name="product-update"),
    path("<uuid:product_id>/delete/",                   DeleteProductView.as_view(),         name="product-delete"),
    path("<uuid:product_id>/images/",                   UploadProductImageView.as_view(),    name="product-images"),
    path("<uuid:product_id>/variants/",                 AddProductVariantView.as_view(),     name="product-variants"),

    # Reviews
    path("<uuid:product_id>/reviews/",                  AddReviewView.as_view(),             name="product-review"),
]