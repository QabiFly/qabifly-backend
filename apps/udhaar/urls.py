from django.urls import path
from .views import (
    MyUdhaarView,
    ShopUdhaarListView,
    RecordUdhaarPaymentView,
    CreateSundayCollectionView,
    SundayCollectionListView,
    AdminUdhaarOverviewView,
)

urlpatterns = [
    path("mine/",                           MyUdhaarView.as_view(),               name="my-udhaar"),
    path("shop/",                           ShopUdhaarListView.as_view(),          name="shop-udhaar"),
    path("pay/",                            RecordUdhaarPaymentView.as_view(),     name="udhaar-pay"),
    path("sunday-collection/",              SundayCollectionListView.as_view(),    name="sunday-collection-list"),
    path("sunday-collection/create/",       CreateSundayCollectionView.as_view(),  name="sunday-collection-create"),
    path("admin/overview/",                 AdminUdhaarOverviewView.as_view(),     name="udhaar-admin-overview"),
]