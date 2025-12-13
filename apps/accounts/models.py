from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid
from datetime import timedelta
from django.utils import timezone


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20, unique=True)
    national_id = models.CharField(max_length=20, unique=True)
    date_of_birth = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    @property
    def roles(self):
        """Return a list of role names for the user."""
        return [ur.role.name for ur in self.userrole_set.all()]

    @property
    def buildings(self):
        """Return a queryset of buildings for the user if they are a union_head."""
        from apps.buildings.models import Building
        return Building.objects.filter(union_head=self)

    def __str__(self):
        return self.full_name or self.email


class Role(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class UserRole(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'role')





class ResidentProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    unit = models.ForeignKey('buildings.Unit', on_delete=models.CASCADE, null=True, blank=True)
    resident_type = models.CharField(max_length=20, default='owner')  # owner or tenant
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='tenants')  # المالك للمستأجر
    rental_start_date = models.DateField(null=True, blank=True)
    rental_end_date = models.DateField(null=True, blank=True)
    rental_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, default='pending')  # pending, approved, rejected, inactive
    rejected_at = models.DateTimeField(null=True, blank=True)
    is_present = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Properties to access unit fields for backward compatibility
    @property
    def floor_number(self):
        return self.unit.floor_number if self.unit else None

    @property
    def apartment_number(self):
        return self.unit.apartment_number if self.unit else None

    @property
    def building(self):
        return self.unit.building if self.unit else None

    @property
    def manual_building_name(self):
        return None  # Not used anymore

    @property
    def manual_address(self):
        return None  # Not used anymore

    def __str__(self):
        if self.unit:
            return f"{self.user.full_name} - {self.unit}"
        return f"{self.user.full_name} - No Building"





class PasswordResetCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_valid(self):
        return not self.is_used and (timezone.now() - self.created_at) < timedelta(minutes=10)

    def __str__(self):
        return f"Reset code for {self.user.email} - {'Used' if self.is_used else 'Valid'}"
