from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Wallet, WalletTransaction, SubscriptionPlan, UserSubscription, Invoice, Transaction
from .serializers import WalletSerializer, WalletTransactionSerializer, SubscriptionPlanSerializer, UserSubscriptionSerializer, InvoiceSerializer, TransactionSerializer
from .services.paymob_service import PaymobService
from .services.sahel_service import SahelService
from mkani.core.permissions import DynamicRolePermission
from mkani.apps.accounts.models import ResidentProfile

class WalletViewSet(viewsets.ModelViewSet):
    permission_classes = [DynamicRolePermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['owner_type', 'owner_id']
    search_fields = ['owner_type']
    ordering_fields = ['current_balance', 'updated_at']

    queryset = Wallet.objects.all()
    serializer_class = WalletSerializer

    def get_queryset(self):
        user = self.request.user
        # Filter wallets based on user roles
        return self.queryset.filter(owner_type='user', owner_id=user.id)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        wallet, created = Wallet.objects.get_or_create(
            owner_type='user',
            owner_id=request.user.id,
            defaults={'current_balance': 0.00}
        )
        serializer = self.get_serializer(wallet)
        return Response(serializer.data)

class WalletTransactionViewSet(viewsets.ModelViewSet):
    permission_classes = [DynamicRolePermission]
    queryset = WalletTransaction.objects.all()
    serializer_class = WalletTransactionSerializer

class SubscriptionPlanViewSet(viewsets.ModelViewSet):
    permission_classes = [DynamicRolePermission]
    queryset = SubscriptionPlan.objects.all()
    serializer_class = SubscriptionPlanSerializer

class UserSubscriptionViewSet(viewsets.ModelViewSet):
    permission_classes = [DynamicRolePermission]
    queryset = UserSubscription.objects.all()
    serializer_class = UserSubscriptionSerializer

class InvoiceViewSet(viewsets.ModelViewSet):
    permission_classes = [DynamicRolePermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['user', 'status']
    search_fields = ['source_type']
    ordering_fields = ['due_date', 'amount']

    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer

class TransactionViewSet(viewsets.ModelViewSet):
    permission_classes = [DynamicRolePermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['wallet', 'status']
    search_fields = ['transaction_reference']
    ordering_fields = ['created_at', 'amount']

    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def initiate_topup(self, request, pk=None):
        transaction = self.get_object()
        billing_data = {
            "first_name": request.user.first_name,
            "last_name": request.user.last_name,
            "email": request.user.email,
            "phone_number": getattr(request.user, 'phone', ''),
        }
        payment_token = PaymobService.process_payment(transaction.amount, billing_data)
        return Response({"payment_token": payment_token}, status=status.HTTP_200_OK)

@api_view(['POST'])
def paymob_webhook(request):
    # Handle Paymob webhook for payment status updates
    data = request.data
    # Process webhook data
    return Response({"status": "received"}, status=status.HTTP_200_OK)

@api_view(['POST'])
def sahel_bill_inquiry(request):
    bill_number = request.data.get('bill_number')
    if not bill_number:
        return Response({"error": "Bill number required"}, status=status.HTTP_400_BAD_REQUEST)
    result = SahelService.inquire_bill(bill_number)
    return Response(result, status=status.HTTP_200_OK)

@api_view(['POST'])
def sahel_bill_payment(request):
    bill_number = request.data.get('bill_number')
    amount = request.data.get('amount')
    if not bill_number or not amount:
        return Response({"error": "Bill number and amount required"}, status=status.HTTP_400_BAD_REQUEST)
    result = SahelService.pay_bill(bill_number, amount)
    return Response(result, status=status.HTTP_200_OK)
