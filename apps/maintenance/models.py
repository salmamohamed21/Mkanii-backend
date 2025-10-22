from django.db import models
from apps.accounts.models import TechnicianProfile, ResidentProfile
from apps.buildings.models import Building

class MaintenanceRequest(models.Model):
    building = models.ForeignKey(Building, on_delete=models.CASCADE)
    resident = models.ForeignKey(ResidentProfile, on_delete=models.CASCADE)
    technician = models.ForeignKey(TechnicianProfile, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField()
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Maintenance ({self.status}) - {self.building.name}"


class MaintenanceInvoice(models.Model):
    maintenance_request = models.OneToOneField(MaintenanceRequest, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Invoice for {self.maintenance_request}"
