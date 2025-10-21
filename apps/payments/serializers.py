from rest_framework import serializers
from .models import Wallet, WalletTransaction, SubscriptionPlan, UserSubscription, Invoice, Transaction

class WalletSerializer(serializers.ModelSerializer):
    owner = serializers.SerializerMethodField()
    recent_transactions = serializers.SerializerMethodField()

    class Meta:
        model = Wallet
        fields = '__all__'

    def get_owner(self, obj):
        if obj.owner_type == 'user':
            from mkani.apps.accounts.models import User
            try:
                user = User.objects.get(id=obj.owner_id)
                return user.full_name
            except User.DoesNotExist:
                return f"User {obj.owner_id}"
        return f"{obj.owner_type} {obj.owner_id}"

    def get_recent_transactions(self, obj):
        # Get last 5 transactions
        transactions = obj.wallettransaction_set.order_by('-created_at')[:5]
        return [
            {
                'id': tx.id,
                'description': tx.description,
                'type': tx.transaction_type,
                'amount': str(tx.amount),
            }
            for tx in transactions
        ]

class WalletTransactionSerializer(serializers.ModelSerializer):
    wallet = WalletSerializer(read_only=True)

    class Meta:
        model = WalletTransaction
        fields = '__all__'

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = '__all__'

class UserSubscriptionSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    plan = SubscriptionPlanSerializer(read_only=True)

    class Meta:
        model = UserSubscription
        fields = '__all__'

class InvoiceSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Invoice
        fields = '__all__'

class TransactionSerializer(serializers.ModelSerializer):
    wallet = WalletSerializer(read_only=True)
    invoice = InvoiceSerializer(read_only=True)

    class Meta:
        model = Transaction
        fields = '__all__'
