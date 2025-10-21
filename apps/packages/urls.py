from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import PackageViewSet, invoice_history, package_types

router = DefaultRouter()
router.register(r'', PackageViewSet)

urlpatterns = [
    path('invoices/history/', invoice_history, name='invoice_history'),
    path('types/', package_types, name='package_types'),
] + router.urls
