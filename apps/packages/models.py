from django.db import models
from apps.accounts.models import User

class Package(models.Model):
    PACKAGE_TYPES = [
        ('utilities', 'Utilities'),
        ('prepaid', 'Prepaid'),
        ('fixed', 'Fixed'),
        ('misc', 'Misc'),
    ]
    package_type = models.CharField(max_length=20, choices=PACKAGE_TYPES)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    is_recurring = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    start_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class PackageUtility(models.Model):
    SERVICE_TYPES = [
        ('electricity', 'Electricity'),
        ('water', 'Water'),
        ('gas', 'Gas'),
        ('internet', 'Internet'),
    ]
    package = models.OneToOneField(Package, on_delete=models.CASCADE)
    service_type = models.CharField(max_length=20, choices=SERVICE_TYPES)
    company_name = models.CharField(max_length=255)
    meter_number = models.CharField(max_length=100)
    customer_code = models.CharField(max_length=100, blank=True, null=True)
    monthly_amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_day = models.PositiveIntegerField()

class PackagePrepaid(models.Model):
    METER_TYPES = [
        ('electricity', 'Electricity'),
        ('water', 'Water'),
    ]
    package = models.OneToOneField(Package, on_delete=models.CASCADE)
    meter_type = models.CharField(max_length=20, choices=METER_TYPES)
    manufacturer = models.CharField(max_length=255)
    meter_number = models.CharField(max_length=100)
    average_monthly_charge = models.DecimalField(max_digits=10, decimal_places=2)

class PackageFixed(models.Model):
    PAYMENT_METHODS = [
        ('union_head', 'Union Head'),
        ('direct_person', 'Direct Person'),
    ]
    package = models.OneToOneField(Package, on_delete=models.CASCADE)
    monthly_amount = models.DecimalField(max_digits=10, decimal_places=2)
    deduction_day = models.PositiveIntegerField()
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    beneficiary = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='beneficiary_packages')
    beneficiary_name = models.CharField(max_length=255, blank=True, null=True)
    beneficiary_phone = models.CharField(max_length=20, blank=True, null=True)
    national_id = models.CharField(max_length=20, blank=True, null=True)

class PackageMisc(models.Model):
    package = models.OneToOneField(Package, on_delete=models.CASCADE)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    deadline = models.DateField()

class PackageBuilding(models.Model):
    package = models.ForeignKey(Package, on_delete=models.CASCADE)
    building = models.ForeignKey('buildings.Building', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('package', 'building')

class PackageInvoice(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
    ]
    PAYMENT_METHODS = [
        ('sahl', 'Sahl'),
        ('fawry', 'Fawry'),
        ('wallet', 'Wallet'),
    ]
    package = models.ForeignKey(Package, on_delete=models.CASCADE)
    building = models.ForeignKey('buildings.Building', on_delete=models.CASCADE)
    resident = models.ForeignKey('accounts.ResidentProfile', on_delete=models.CASCADE, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, blank=True, null=True)
    transaction = models.ForeignKey('payments.Transaction', on_delete=models.SET_NULL, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.package.name} - {self.building.name} - {self.amount}"


