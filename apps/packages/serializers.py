from rest_framework import serializers
from .models import Package, PackageUtility, PackagePrepaid, PackageFixed, PackageMisc, PackageBuilding, PackageInvoice

class PackageBuildingSerializer(serializers.ModelSerializer):
    building_name = serializers.CharField(source="building.name", read_only=True)

    class Meta:
        model = PackageBuilding
        fields = ["building", "building_name"]

class PackageUtilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = PackageUtility
        fields = "__all__"

class PackagePrepaidSerializer(serializers.ModelSerializer):
    class Meta:
        model = PackagePrepaid
        fields = "__all__"

class PackageFixedSerializer(serializers.ModelSerializer):
    beneficiary_name = serializers.CharField(source="beneficiary.full_name", read_only=True)

    class Meta:
        model = PackageFixed
        fields = "__all__"

class PackageMiscSerializer(serializers.ModelSerializer):
    class Meta:
        model = PackageMisc
        fields = "__all__"

class PackageSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source="created_by.full_name", read_only=True)
    buildings = PackageBuildingSerializer(source="packagebuilding_set", many=True, read_only=True)
    utility_details = PackageUtilitySerializer(source="packageutility", read_only=True)
    prepaid_details = PackagePrepaidSerializer(source="packageprepaid", read_only=True)
    fixed_details = PackageFixedSerializer(source="packagefixed", read_only=True)
    misc_details = PackageMiscSerializer(source="packagemisc", read_only=True)

    class Meta:
        model = Package
        fields = [
            "id", "package_type", "name", "description", "is_recurring",
            "created_by", "created_by_name", "start_date", "created_at", "updated_at",
            "buildings", "utility_details", "prepaid_details", "fixed_details", "misc_details"
        ]

    def create(self, validated_data):
        request = self.context.get('request')
        package_type = validated_data.get('package_type')
        package = Package.objects.create(**validated_data)

        # Create specific details based on package type
        if package_type == 'utilities':
            PackageUtility.objects.create(package=package, **request.data.get('utility_details', {}))
        elif package_type == 'prepaid':
            PackagePrepaid.objects.create(package=package, **request.data.get('prepaid_details', {}))
        elif package_type == 'fixed':
            PackageFixed.objects.create(package=package, **request.data.get('fixed_details', {}))
        elif package_type == 'misc':
            PackageMisc.objects.create(package=package, **request.data.get('misc_details', {}))

        return package

class PackageInvoiceSerializer(serializers.ModelSerializer):
    package_name = serializers.CharField(source="package.name", read_only=True)
    building_name = serializers.CharField(source="building.name", read_only=True)
    resident_name = serializers.CharField(source="resident.user.full_name", read_only=True)

    class Meta:
        model = PackageInvoice
        fields = [
            "id", "package", "package_name", "building", "building_name",
            "resident", "resident_name", "amount", "due_date", "status",
            "payment_method", "transaction", "created_at", "updated_at"
        ]
