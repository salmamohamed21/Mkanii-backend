from rest_framework import serializers
from .models import MaintenanceRequest
from apps.accounts.models import TechnicianProfile, ResidentProfile
from apps.buildings.models import Building


class MaintenanceRequestSerializer(serializers.ModelSerializer):
    technician_name = serializers.CharField(source="technician.user.full_name", read_only=True)
    building_name = serializers.CharField(source="building.name", read_only=True)
    resident_name = serializers.CharField(source="resident.user.full_name", read_only=True)

    class Meta:
        model = MaintenanceRequest
        fields = "__all__"


class CreateMaintenanceRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaintenanceRequest
        fields = ["building", "description"]

    def create(self, validated_data):
        request = self.context["request"]
        resident_profile = ResidentProfile.objects.filter(user=request.user).first()
        if not resident_profile:
            raise serializers.ValidationError("Resident profile not found for the user.")
        return MaintenanceRequest.objects.create(
            building=validated_data["building"],
            resident=resident_profile,
            description=validated_data["description"],
            status="pending",
        )

