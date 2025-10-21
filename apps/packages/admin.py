from django.contrib import admin
from .models import Package, PackageUtility, PackagePrepaid, PackageFixed, PackageMisc, PackageBuilding, PackageInvoice

@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ("name", "package_type", "is_recurring", "created_by", "start_date", "created_at")
    list_filter = ("package_type", "is_recurring")
    search_fields = ("name",)

@admin.register(PackageUtility)
class PackageUtilityAdmin(admin.ModelAdmin):
    list_display = ("package", "service_type", "company_name", "meter_number", "monthly_amount", "due_day")
    list_filter = ("service_type",)
    search_fields = ("package__name", "company_name", "meter_number")

@admin.register(PackagePrepaid)
class PackagePrepaidAdmin(admin.ModelAdmin):
    list_display = ("package", "meter_type", "manufacturer", "meter_number", "average_monthly_charge")
    list_filter = ("meter_type",)
    search_fields = ("package__name", "manufacturer", "meter_number")

@admin.register(PackageFixed)
class PackageFixedAdmin(admin.ModelAdmin):
    list_display = ("package", "monthly_amount", "deduction_day", "payment_method", "beneficiary_name")
    list_filter = ("payment_method",)
    search_fields = ("package__name", "beneficiary_name")

@admin.register(PackageMisc)
class PackageMiscAdmin(admin.ModelAdmin):
    list_display = ("package", "total_amount", "payment_date", "deadline")
    search_fields = ("package__name",)

@admin.register(PackageBuilding)
class PackageBuildingAdmin(admin.ModelAdmin):
    list_display = ("package", "building")
    list_filter = ("building",)
    search_fields = ("package__name", "building__name")

@admin.register(PackageInvoice)
class PackageInvoiceAdmin(admin.ModelAdmin):
    list_display = ("package", "building", "resident", "amount", "due_date", "status", "payment_method")
    list_filter = ("status", "payment_method", "due_date")
    search_fields = ("package__name", "building__name", "resident__user__full_name")
