from django.db import models
from apps.accounts.models import User
import uuid


class RentalListing(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    unit = models.ForeignKey('buildings.Unit', on_delete=models.CASCADE)
    building = models.ForeignKey('buildings.Building', on_delete=models.CASCADE)
    daily_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    yearly_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    comment = models.TextField(null=True, blank=True)
    # المستأجر لو في طلب أو موافقة
    tenant = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="rented_units")
    request_status = models.CharField(max_length=20, default="none")
    # none – requested – approved – rejected
    # حالة الإعلان
    status = models.CharField(max_length=20, default="available")
    # available – rented – cancelled
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
