from django.urls import path
from .views import (
    MyWalletView,
    WalletTransactionsView,
    TopUpWalletView,
    AdminCreditWalletView,
    RequestWithdrawalView,
    MyWithdrawalsView,
    AdminWithdrawalsView,
    AdminProcessWithdrawalView,
)

urlpatterns = [
    path("",                                    MyWalletView.as_view(),              name="wallet"),
    path("transactions/",                       WalletTransactionsView.as_view(),    name="wallet-transactions"),
    path("topup/",                              TopUpWalletView.as_view(),           name="wallet-topup"),
    path("withdraw/",                           RequestWithdrawalView.as_view(),     name="wallet-withdraw"),
    path("withdrawals/",                        MyWithdrawalsView.as_view(),         name="my-withdrawals"),
    path("admin/credit/",                       AdminCreditWalletView.as_view(),     name="admin-wallet-credit"),
    path("admin/withdrawals/",                  AdminWithdrawalsView.as_view(),      name="admin-withdrawals"),
    path("admin/withdrawals/<uuid:withdrawal_id>/process/",
         AdminProcessWithdrawalView.as_view(),  name="admin-process-withdrawal"),
]