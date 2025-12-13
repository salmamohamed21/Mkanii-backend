from rest_framework import serializers
from .models import RentalListing
from apps.buildings.models import Unit, Building
from apps.accounts.models import User


class RentalListingSerializer(serializers.ModelSerializer):
    unit_details = serializers.SerializerMethodField()
    building_details = serializers.SerializerMethodField()
    owner_details = serializers.SerializerMethodField()
    tenant_details = serializers.SerializerMethodField()

    class Meta:
        model = RentalListing
        fields = [
            'id', 'unit', 'building', 'daily_price', 'monthly_price', 'yearly_price',
            'comment', 'tenant', 'request_status', 'status', 'created_at', 'updated_at',
            'unit_details', 'building_details', 'owner_details', 'tenant_details'
        ]
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']

    def get_unit_details(self, obj):
        return {
            'id': obj.unit.id,
            'unit_number': obj.unit.apartment_number,
            'area': obj.unit.area,
            'rooms': obj.unit.rooms_count,
            'floor': obj.unit.floor_number
        }

    def get_building_details(self, obj):
        return {
            'id': obj.building.id,
            'name': obj.building.name,
            'address': obj.building.address,
            'latitude': obj.building.latitude,
            'longitude': obj.building.longitude
        }

    def get_owner_details(self, obj):
        return {
            'id': obj.owner.id,
            'email': obj.owner.email,
            'first_name': obj.owner.first_name,
            'last_name': obj.owner.last_name,
            'phone_number': obj.owner.phone_number
        }

    def get_tenant_details(self, obj):
        if obj.tenant:
            return {
                'id': obj.tenant.id,
                'email': obj.tenant.email,
                'first_name': obj.tenant.first_name,
                'last_name': obj.tenant.last_name
            }
        return None

    def create(self, validated_data):
        # Set owner to current user
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)


class RentalListingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RentalListing
        fields = ['unit', 'building', 'daily_price', 'monthly_price', 'yearly_price', 'comment']

    def validate(self, data):
        # Ensure at least one price is provided
        prices = [data.get('daily_price'), data.get('monthly_price'), data.get('yearly_price')]
        if not any(price is not None for price in prices):
            raise serializers.ValidationError("At least one price (daily, monthly, or yearly) must be provided.")
        return data


class RentalRequestSerializer(serializers.Serializer):
    listing_id = serializers.UUIDField()

    def validate_listing_id(self, value):
        try:
            listing = RentalListing.objects.get(id=value, status='available')
            if listing.tenant:
                raise serializers.ValidationError("This listing already has a tenant.")
        except RentalListing.DoesNotExist:
            raise serializers.ValidationError("Listing not found or not available.")
        return value


class RentalApprovalSerializer(serializers.Serializer):
    listing_id = serializers.UUIDField()
    action = serializers.ChoiceField(choices=['approve', 'reject'])

    def validate_listing_id(self, value):
        try:
            listing = RentalListing.objects.get(id=value, status='available', request_status='requested')
            if not listing.tenant:
                raise serializers.ValidationError("No tenant has requested this listing.")
        except RentalListing.DoesNotExist:
            raise serializers.ValidationError("Listing not found or not in requested state.")
        return value
