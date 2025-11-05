from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid
from datetime import timedelta
from django.utils import timezone


class User(AbstractUser):
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
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class UserRole(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'role')





class ResidentProfile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    unit = models.ForeignKey('buildings.Unit', on_delete=models.CASCADE, null=True, blank=True)
    resident_type = models.CharField(max_length=20, default='owner')  # owner or tenant
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='tenants')  # المالك للمستأجر
    area = models.FloatField(null=True, blank=True)  # مساحة الشقة بالمتر المربع
    rooms_count = models.PositiveIntegerField(null=True, blank=True)  # عدد الغرف في الشقة
    rental_start_date = models.DateField(null=True, blank=True)
    rental_end_date = models.DateField(null=True, blank=True)
    rental_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, default='active')  # pending, approved, rejected, inactive
    is_present = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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
