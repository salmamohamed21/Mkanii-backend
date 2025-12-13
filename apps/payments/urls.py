from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    WalletViewSet, WalletTransactionViewSet, SubscriptionPlanViewSet,
    UserSubscriptionViewSet, InvoiceViewSet, TransactionViewSet,
    paymob_webhook, sahel_bill_inquiry, sahel_bill_payment, pay_rent
)

router = DefaultRouter()
router.register(r'wallets', WalletViewSet)
router.register(r'wallet-transactions', WalletTransactionViewSet)
router.register(r'subscription-plans', SubscriptionPlanViewSet)
router.register(r'user-subscriptions', UserSubscriptionViewSet)
router.register(r'invoices', InvoiceViewSet)
router.register(r'transactions', TransactionViewSet)

urlpatterns = router.urls + [
    path('webhook/paymob/', paymob_webhook, name='paymob_webhook'),
    path('sahel/inquire/', sahel_bill_inquiry, name='sahel_inquire'),
    path('sahel/pay/', sahel_bill_payment, name='sahel_pay'),
    path('rent/pay/', pay_rent, name='pay_rent'),
]
