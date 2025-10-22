from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters
from rest_framework.decorators import action, api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from .models import Building
from .serializers import BuildingSerializer
from apps.core.permissions import DynamicRolePermission
from apps.core.views import PublicAPIView



class BuildingViewSet(viewsets.ModelViewSet):
    permission_classes = [DynamicRolePermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['name', 'address']
    search_fields = ['name', 'address']
    ordering_fields = ['name', 'address']

    queryset = Building.objects.all().order_by('created_at')
    serializer_class = BuildingSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'address']
    ordering_fields = ['name', 'address']

    def get_queryset(self):
        roles = getattr(self.request.user, 'roles', None)
        if hasattr(roles, 'all'):
            role_names = [r.name for r in roles.all()]
        else:
            role_names = []

        if 'union_head' in role_names:
            return Building.objects.filter(union_head=self.request.user).order_by('created_at')
        return Building.objects.all().order_by('created_at')

    def perform_create(self, serializer):
        serializer.save(union_head=self.request.user)

    @action(detail=False, methods=['get'], permission_classes=[DynamicRolePermission])
    def recent(self, request):
        qs = self.get_queryset().order_by('-id')[:10]
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], permission_classes=[DynamicRolePermission])
    def residents_requests(self, request, pk=None):
        building = self.get_object()
        from apps.accounts.models import ResidentProfile
        requests = ResidentProfile.objects.filter(building=building, status='pending')
        data = list(requests.values('id', 'user__full_name', 'floor_number', 'apartment_number', 'resident_type', 'created_at'))
        return Response(data)

    @action(detail=True, methods=['post'], permission_classes=[DynamicRolePermission])
    def accept_request(self, request, pk=None):
        building = self.get_object()
        request_id = request.data.get('requestId')
        action = request.data.get('action')
        rejection_reason = request.data.get('rejectionReason')
        try:
            from apps.accounts.models import ResidentProfile
            from apps.notifications.models import Notification
            from django.utils import timezone
            resident_profile = ResidentProfile.objects.get(id=request_id, building=building, status='pending')
            if action == 'accept':
                resident_profile.status = 'accepted'
                # Send notification to resident
                Notification.objects.create(
                    user=resident_profile.user,
                    title="تم قبول طلب الانضمام",
                    message=f"تم قبول طلبك للانضمام إلى العمارة {building.name} من قبل رئيس الاتحاد {request.user.full_name}"
                )
            elif action == 'reject':
                resident_profile.status = 'rejected'
                # Send notification to resident with rejection reason
                message = f"تم رفض طلبك للانضمام إلى العمارة {building.name} من قبل رئيس الاتحاد {request.user.full_name}"
                if rejection_reason:
                    message += f". السبب: {rejection_reason}"
                Notification.objects.create(
                    user=resident_profile.user,
                    title="تم رفض طلب الانضمام",
                    message=message
                )
            resident_profile.save()
            return Response({'message': f'Request {action}ed successfully'})
        except ResidentProfile.DoesNotExist:
            return Response({'error': 'Request not found'}, status=404)

    @action(detail=True, methods=['get'], permission_classes=[DynamicRolePermission])
    def resident_details(self, request, pk=None):
        """
        Get detailed information for a specific resident in the building, including payment history.
        """
        building = self.get_object()
        resident_id = request.query_params.get('resident_id')
        if not resident_id:
            return Response({'error': 'resident_id parameter required'}, status=400)

        try:
            from apps.accounts.models import ResidentProfile
            resident = ResidentProfile.objects.get(id=resident_id, building=building)
            # Get payment history
            from apps.packages.models import PackageInvoice
            payments = PackageInvoice.objects.filter(
                resident=resident
            ).select_related('package').values(
                'id', 'package__name', 'amount', 'due_date', 'status'
            )
            data = {
                'id': resident.id,
                'user_name': resident.user.full_name,
                'phone_number': resident.user.phone_number,
                'national_id': resident.user.national_id,
                'floor_number': resident.floor_number,
                'apartment_number': resident.apartment_number,
                'resident_type': resident.get_resident_type_display(),
                'created_at': resident.created_at.isoformat(),
                'payment_history': list(payments)
            }
            return Response(data)
        except ResidentProfile.DoesNotExist:
            return Response({'error': 'Resident not found in this building'}, status=404)

    @action(detail=False, methods=['get'], permission_classes=[DynamicRolePermission], url_path='my-buildings')
    def my_buildings(self, request):
        """
        Get buildings for the current union_head user only.
        """
        roles = getattr(request.user, 'roles', None)
        if hasattr(roles, 'all'):
            roles = [r.name for r in roles.all()]
        elif not isinstance(roles, list):
            roles = [str(roles)]

        # Handle case where roles might be stored as strings like "['union_head']"
        flattened_roles = []
        for role in roles:
            if isinstance(role, str) and role.startswith('[') and role.endswith(']'):
                # Parse the string list
                try:
                    import ast
                    parsed = ast.literal_eval(role)
                    flattened_roles.extend(parsed)
                except:
                    flattened_roles.append(role.strip("[]'\""))
            else:
                flattened_roles.append(role)

        if 'union_head' not in flattened_roles:
            return Response({'error': 'Access denied. Only union heads can access this endpoint.'}, status=403)

        buildings = Building.objects.filter(union_head_id=request.user.id).order_by('created_at')

        print("🔍 Authenticated user:", request.user.id, request.user.email)
        print("🏢 Found buildings:", buildings.count())

        serializer = self.get_serializer(buildings, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], permission_classes=[DynamicRolePermission], url_path='accepted-residents')
    def accepted_residents(self, request, pk=None):
        """
        Get accepted residents for a specific building (union_head only).
        """
        building = self.get_object()

        # Check if user is union_head of this building
        if building.union_head != request.user:
            return Response({'error': 'Access denied. Only the union head can view residents.'}, status=403)

        from apps.accounts.models import ResidentProfile
        from apps.packages.models import PackageInvoice

        residents = ResidentProfile.objects.filter(
            building=building,
            status='accepted'
        ).select_related('user')

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
                'national_id': resident.user.national_id,
                'floor_number': resident.floor_number,
                'apartment_number': resident.apartment_number,
                'resident_type': resident.get_resident_type_display(),
                'building_name': building.name,
                'created_at': resident.created_at.isoformat(),
                'payment_history': list(payments)
            })

        return Response(resident_data)

    @action(detail=False, methods=['get'], permission_classes=[DynamicRolePermission])
    def resident_building(self, request):
        """
        Get the building details for the current resident user.
        """
        try:
            from apps.accounts.models import ResidentProfile
            resident_profile = ResidentProfile.objects.get(user=request.user)
            building = resident_profile.building
            serializer = self.get_serializer(building)
            return Response(serializer.data)
        except ResidentProfile.DoesNotExist:
            return Response({'error': 'Resident profile not found'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=500)


class PublicBuildingNamesView(PublicAPIView):
    """
    🔹 Endpoint: /api/public/building-names/
    🔹 الهدف: عرض أسماء وعناوين العمارات المتاحة للجميع (بدون تسجيل دخول)
    """
    def get(self, request):
        print("🔍 user:", request.user)
        print("🔍 auth:", request.auth)
        from .models import Building
        buildings = Building.objects.filter(approval_status='approved')
        data = list(buildings.values('id', 'name', 'address'))
        return Response(data)


class PublicBuildingsListView(PublicAPIView):
    """
    🔹 Endpoint: /api/public/public-buildings-list/
    🔹 الهدف: عرض أسماء وعناوين العمارات المتاحة للجميع (بدون تسجيل دخول)
    """
    def get(self, request):
        buildings = Building.objects.all()
        data = list(buildings.values('id', 'name', 'address'))
        return Response(data)



