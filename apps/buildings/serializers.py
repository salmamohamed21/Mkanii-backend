from rest_framework import serializers
from .models import Building

class BuildingSerializer(serializers.ModelSerializer):
    residents = serializers.SerializerMethodField()
    union_head_name = serializers.SerializerMethodField()
    packages_count = serializers.SerializerMethodField()
    packages = serializers.SerializerMethodField()

    class Meta:
        model = Building
        fields = [
            'id', 'name', 'address', 'total_units', 'total_floors', 'units_per_floor',
            'subscription_plan', 'union_head', 'union_head_name', 'created_at', 'updated_at',
            'residents', 'packages_count', 'packages'
        ]

    def get_residents(self, obj):
        from apps.accounts.models import ResidentProfile
        from apps.packages.models import PackageInvoice

        residents = ResidentProfile.objects.filter(building=obj).select_related('user')
        resident_data = []

        for resident in residents:
            payments = PackageInvoice.objects.filter(
                resident=resident,
                status='paid'
            ).select_related('package').values(
                'id', 'package__name', 'amount', 'due_date', 'status'
            )

            resident_data.append({
                'id': resident.id,
                'user_name': resident.user.full_name,
                'phone_number': resident.user.phone_number,
                'floor_number': resident.floor_number,
                'apartment_number': resident.apartment_number,
                'resident_type': getattr(resident, 'resident_type', 'unknown'),
                'national_id': resident.user.national_id,
                'payment_history': list(payments)
            })

        return resident_data

    def get_union_head_name(self, obj):
        return obj.union_head.full_name if getattr(obj, 'union_head', None) else None

    def get_packages_count(self, obj):
        from apps.packages.models import PackageBuilding
        return PackageBuilding.objects.filter(building=obj).count()

    def get_packages(self, obj):
        from apps.packages.models import PackageBuilding, Package, PackageFixed, PackageUtility, PackagePrepaid, PackageMisc
        package_buildings = PackageBuilding.objects.filter(building=obj).select_related('package')
        packages_data = []
        for pb in package_buildings:
            package = pb.package
            amount = None
            if package.package_type == 'fixed':
                try:
                    fixed_details = PackageFixed.objects.get(package=package)
                    amount = fixed_details.monthly_amount
                except PackageFixed.DoesNotExist:
                    pass
            elif package.package_type == 'utilities':
                try:
                    utility_details = PackageUtility.objects.get(package=package)
                    amount = utility_details.monthly_amount
                except PackageUtility.DoesNotExist:
                    pass
            elif package.package_type == 'prepaid':
                try:
                    prepaid_details = PackagePrepaid.objects.get(package=package)
                    amount = prepaid_details.average_monthly_charge
                except PackagePrepaid.DoesNotExist:
                    pass
            elif package.package_type == 'misc':
                try:
                    misc_details = PackageMisc.objects.get(package=package)
                    amount = misc_details.total_amount
                except PackageMisc.DoesNotExist:
                    pass

            packages_data.append({
                'id': package.id,
                'name': package.name,
                'description': package.description,
                'package_type': package.package_type,
                'is_recurring': package.is_recurring,
                'amount': amount,
                'created_at': package.created_at.isoformat(),
            })
        return packages_data




