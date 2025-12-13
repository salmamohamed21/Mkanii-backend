from django.db import models
from apps.accounts.models import User
import uuid

class Building(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    union_head = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='buildings')
    name = models.CharField(max_length=255)
    address = models.TextField()
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    total_units = models.PositiveIntegerField()
    total_floors = models.PositiveIntegerField()
    units_per_floor = models.PositiveIntegerField()
    subscription_plan = models.CharField(max_length=50, null=True, blank=True)
    approval_status = models.CharField(max_length=20, default='approved')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Unit(models.Model):
    building = models.ForeignKey(Building, on_delete=models.CASCADE)
    floor_number = models.PositiveIntegerField()
    apartment_number = models.CharField(max_length=10)
    area = models.FloatField(null=True, blank=True)  # مساحة الوحدة بالمتر المربع
    rooms_count = models.PositiveIntegerField(null=True, blank=True)  # عدد الغرف في الوحدة
    status = models.CharField(max_length=20, default='available')

    def __str__(self):
        return f"{self.building.name} - Floor {self.floor_number} - Apt {self.apartment_number}"



