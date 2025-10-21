from django.contrib import admin
from .models import MaintenanceRequest, MaintenanceInvoice

@admin.register(MaintenanceRequest)
class MaintenanceRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "building", "technician", "status", "created_at")
    list_filter = ("status", "building")
    search_fields = ("description", "building__name")

@admin.register(MaintenanceInvoice)
class MaintenanceInvoiceAdmin(admin.ModelAdmin):
    list_display = ("maintenance_request", "amount", "status", "created_at")
    list_filter = ("status",)
