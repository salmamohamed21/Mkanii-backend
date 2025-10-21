from django.db import models
from mkani.apps.accounts.models import User

class Building(models.Model):
    union_head = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='buildings')
    name = models.CharField(max_length=255)
    address = models.TextField()
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    total_units = models.PositiveIntegerField()
    total_floors = models.PositiveIntegerField()
    units_per_floor = models.PositiveIntegerField()
    subscription_plan = models.CharField(max_length=50)
    approval_status = models.CharField(max_length=20, default='approved')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
