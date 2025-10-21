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
    roles = models.ManyToManyField('Role', related_name='users', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.full_name or self.email


class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class UserDocument(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    document_type = models.CharField(max_length=100)
    file_path = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.full_name} - {self.document_type}"


class ResidentProfile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    building = models.ForeignKey('buildings.Building', on_delete=models.CASCADE, null=True, blank=True)
    floor_number = models.PositiveIntegerField(null=True, blank=True)
    apartment_number = models.CharField(max_length=10, null=True, blank=True)
    RESIDENT_TYPE_CHOICES = [
        ('owner', 'مالك'),
        ('tenant', 'مستأجر'),
    ]
    resident_type = models.CharField(max_length=20, choices=RESIDENT_TYPE_CHOICES, default='owner')
    owner_national_id = models.CharField(max_length=20, null=True, blank=True)  # For tenant
    manual_building_name = models.CharField(max_length=255, null=True, blank=True)
    manual_address = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, default='pending')  # pending, accepted, rejected, not_found
    is_present = models.BooleanField(default=True)  # Track resident presence
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.full_name} - {self.building.name}"


class TechnicianProfile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    specialization = models.CharField(max_length=100)
    work_area = models.CharField(max_length=255)
    employment_status = models.CharField(max_length=20)
    services_description = models.TextField(blank=True)
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.full_name} - {self.specialization}"


class TechnicianSchedule(models.Model):
    technician = models.ForeignKey(TechnicianProfile, on_delete=models.CASCADE)
    day_of_week = models.CharField(max_length=20)
    start_time = models.TimeField()
    end_time = models.TimeField()
    shift_type = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.technician.user.full_name} - {self.day_of_week}"


class PasswordResetCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_valid(self):
        return not self.is_used and (timezone.now() - self.created_at) < timedelta(minutes=10)

    def __str__(self):
        return f"Reset code for {self.user.email} - {'Used' if self.is_used else 'Valid'}"
