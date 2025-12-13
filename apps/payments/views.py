from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Wallet, WalletTransaction, SubscriptionPlan, UserSubscription, Invoice, Transaction
from .serializers import WalletSerializer, WalletTransactionSerializer, SubscriptionPlanSerializer, UserSubscriptionSerializer, InvoiceSerializer, TransactionSerializer
from .services.paymob_service import PaymobService
from .services.sahel_service import SahelService
from apps.core.permissions import DynamicRolePermission
from apps.accounts.models import ResidentProfile

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


from django.db import transaction
from apps.accounts.models import User
from decimal import Decimal

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def pay_rent(request):
    """
    Handles a rent payment from a tenant to a landlord.
    """
    tenant = request.user
    landlord_id = request.data.get('landlord_id')
    # The frontend sends 'apartment_id', which is actually the resident_profile_id.
    resident_profile_id = request.data.get('apartment_id')
    try:
        amount = Decimal(request.data.get('amount'))
    except (TypeError, ValueError):
        return Response({"error": "Invalid amount provided."}, status=status.HTTP_400_BAD_REQUEST)

    if not all([landlord_id, resident_profile_id, amount]):
        return Response({"error": "Missing required fields: landlord_id, apartment_id, amount."}, status=status.HTTP_400_BAD_REQUEST)

    if amount <= 0:
        return Response({"error": "Amount must be positive."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        resident_profile = ResidentProfile.objects.get(id=resident_profile_id, user=tenant)
    except ResidentProfile.DoesNotExist:
        return Response({"error": "Rental profile not found for this user."}, status=status.HTTP_404_NOT_FOUND)

    if str(resident_profile.owner.id) != landlord_id:
        return Response({"error": "Landlord ID does not match the owner of this rental profile."}, status=status.HTTP_403_FORBIDDEN)

    try:
        landlord = User.objects.get(id=landlord_id)
        tenant_wallet, _ = Wallet.objects.get_or_create(owner_id=tenant.id, owner_type='user')
        landlord_wallet, _ = Wallet.objects.get_or_create(owner_id=landlord.id, owner_type='user')
    except User.DoesNotExist:
        return Response({"error": "Could not find landlord user."}, status=status.HTTP_404_NOT_FOUND)

    if tenant_wallet.current_balance < amount:
        return Response({"error": "Insufficient balance."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        with transaction.atomic():
            # Debit tenant's wallet
            tenant_wallet.current_balance -= amount
            tenant_wallet.save()
            Transaction.objects.create(
                wallet=tenant_wallet,
                amount=-amount,
                transaction_type='rent_payment',
                status='completed',
                description=f'Rent payment to {landlord.full_name} for unit {resident_profile.unit}.'
            )

            # Credit landlord's wallet
            landlord_wallet.current_balance += amount
            landlord_wallet.save()
            Transaction.objects.create(
                wallet=landlord_wallet,
                amount=amount,
                transaction_type='rent_received',
                status='completed',
                description=f'Rent received from {tenant.full_name} for unit {resident_profile.unit}.'
            )
            
            # Optionally create an Invoice
            Invoice.objects.create(
                user=tenant,
                amount=amount,
                status='paid',
                source_id=resident_profile.id,
                source_type='rent',
                description=f'Rent for {resident_profile.unit}'
            )

    except Exception as e:
        # Log the exception e
        return Response({"error": "An error occurred during the transaction."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({"message": "Rent paid successfully."}, status=status.HTTP_200_OK)
