from django.contrib import admin
from .models import Wallet, WalletTransaction, SubscriptionPlan, UserSubscription, Invoice, Transaction

# Register models for admin
admin.site.register(Wallet)
admin.site.register(WalletTransaction)
admin.site.register(SubscriptionPlan)
admin.site.register(UserSubscription)
admin.site.register(Invoice)
admin.site.register(Transaction)
