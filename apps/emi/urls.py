from django.urls import path
from .views import (
    CreateEMIPlanView,
    MyEMIPlansView,
    PayEMIInstallmentView,
    AdminEMIOverviewView,
)

urlpatterns = [
    path("create/",          CreateEMIPlanView.as_view(),      name="emi-create"),
    path("mine/",            MyEMIPlansView.as_view(),          name="my-emi"),
    path("pay/",             PayEMIInstallmentView.as_view(),   name="emi-pay"),
    path("admin/overview/",  AdminEMIOverviewView.as_view(),    name="emi-admin-overview"),
]