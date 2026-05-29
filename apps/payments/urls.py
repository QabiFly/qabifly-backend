from django.urls import path
from .views import (
    GetUPIDeepLinkView,
    SubmitUTRView,
    AdminVerifyPaymentView,
    MyPaymentsView,
    AdminPendingPaymentsView,
)

urlpatterns = [
    path("upi/<str:order_number>/",          GetUPIDeepLinkView.as_view(),      name="upi-deeplink"),
    path("upi/submit-utr/",                  SubmitUTRView.as_view(),            name="upi-submit-utr"),
    path("mine/",                            MyPaymentsView.as_view(),           name="my-payments"),
    path("admin/<str:order_number>/verify/", AdminVerifyPaymentView.as_view(),   name="admin-verify-payment"),
    path("admin/pending/",                   AdminPendingPaymentsView.as_view(), name="admin-pending-payments"),
]