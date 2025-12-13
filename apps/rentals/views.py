from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q
from .models import RentalListing
from .serializers import RentalListingSerializer, RentalListingCreateSerializer, RentalRequestSerializer, RentalApprovalSerializer
from apps.core.permissions import DynamicRolePermission


class RentalListingViewSet(viewsets.ModelViewSet):
    queryset = RentalListing.objects.all()
    permission_classes = [DynamicRolePermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'request_status', 'building']
    search_fields = ['building__name', 'unit__unit_number', 'comment']
    ordering_fields = ['created_at', 'daily_price', 'monthly_price', 'yearly_price']

    def get_serializer_class(self):
        if self.action == 'create':
            return RentalListingCreateSerializer
        return RentalListingSerializer

    def get_queryset(self):
        user = self.request.user
        # Get roles from database
        roles = [ur.role.name for ur in user.userrole_set.all()]

        # Add implied roles based on profiles
        from apps.accounts.models import ResidentProfile
        is_resident = ResidentProfile.objects.filter(user=user).exists()
        is_union_head = RentalListing.objects.filter(building__union_head=user).exists()

        if is_resident and 'resident' not in roles:
            roles.append('resident')
        if is_union_head and 'union_head' not in roles:
            roles.append('union_head')

        # Superusers and staff should see all listings
        if user.is_superuser or user.is_staff:
            return RentalListing.objects.all().order_by('-created_at')

        query = Q()
        if 'union_head' in roles:
            # Listings in buildings where user is union_head
            query |= Q(building__union_head=user)

        if 'resident' in roles:
            try:
                resident_profile = ResidentProfile.objects.filter(user=user).first()
                if resident_profile and resident_profile.unit and resident_profile.unit.building:
                    # Listings in the building where user is a resident
                    query |= Q(building=resident_profile.unit.building)
            except Exception:
                pass  # Not a resident, or profile incomplete

        # Users can see their own listings
        query |= Q(owner=user)

        if query:
            return RentalListing.objects.filter(query).distinct().order_by('-created_at')

        # For other authenticated users, return no listings
        return RentalListing.objects.none()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_listings(self, request):
        """
        Get rental listings created by the current user.
        """
        listings = RentalListing.objects.filter(owner=request.user).order_by('-created_at')
        serializer = self.get_serializer(listings, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def request_rental(self, request):
        """
        Allow a resident to request to rent a listing.
        """
        serializer = RentalRequestSerializer(data=request.data)
        if serializer.is_valid():
            listing_id = serializer.validated_data['listing_id']
            listing = RentalListing.objects.get(id=listing_id)
            listing.tenant = request.user
            listing.request_status = 'requested'
            listing.save()
            return Response({'message': 'Rental request submitted successfully'})
        return Response(serializer.errors, status=400)

    @action(detail=False, methods=['post'], permission_classes=[DynamicRolePermission])
    def approve_rental(self, request):
        """
        Allow union_head to approve or reject rental requests.
        """
        serializer = RentalApprovalSerializer(data=request.data)
        if serializer.is_valid():
            listing_id = serializer.validated_data['listing_id']
            action = serializer.validated_data['action']
            listing = RentalListing.objects.get(id=listing_id)

            if action == 'approve':
                listing.request_status = 'approved'
                listing.status = 'rented'
                message = 'Rental request approved'
            elif action == 'reject':
                listing.request_status = 'rejected'
                listing.tenant = None
                message = 'Rental request rejected'

            listing.save()
            return Response({'message': message})
        return Response(serializer.errors, status=400)
