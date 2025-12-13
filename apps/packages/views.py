from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Package, PackageBuilding, PackageInvoice
from .serializers import PackageSerializer
from apps.packages.tasks import generate_monthly_invoices
from apps.core.permissions import DynamicRolePermission

class PackageViewSet(viewsets.ModelViewSet):
    permission_classes = [DynamicRolePermission]
    queryset = Package.objects.all().select_related("created_by")
    serializer_class = PackageSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["package_type", "is_recurring"]
    search_fields = ["name"]
    ordering_fields = ["created_at", "start_date"]

    def get_queryset(self):
        user = self.request.user
        queryset = Package.objects.all().select_related("created_by")

        # Get roles from database
        roles = [ur.role.name for ur in user.userrole_set.all()]

        # Add implied roles based on profiles
        from apps.accounts.models import ResidentProfile
        from apps.buildings.models import Building
        is_resident = ResidentProfile.objects.filter(user=user).exists()
        is_union_head = Building.objects.filter(union_head=user).exists()

        if is_resident and 'resident' not in roles:
            roles.append('resident')
        if is_union_head and 'union_head' not in roles:
            roles.append('union_head')

        # ✅ فلترة حسب building_id لو متبعت في الـ request
        building_id = self.request.query_params.get('building_id')

        # ✅ باقي الفلترة حسب الدور
        if 'resident' in roles:
            try:
                resident_profile = user.resident_profiles.first()
                if resident_profile and resident_profile.building:
                    allowed_building_id = resident_profile.building.id
                    if building_id:
                        # If building_id is provided, check if it matches the resident's building
                        if building_id == str(allowed_building_id):
                            queryset = queryset.filter(packagebuilding__building_id=building_id).distinct()
                        else:
                            queryset = Package.objects.none()
                    else:
                        queryset = queryset.filter(packagebuilding__building_id=allowed_building_id).distinct()
                else:
                    queryset = Package.objects.none()
            except:
                queryset = Package.objects.none()

        elif 'union_head' in roles:
            building_ids = user.buildings.values_list('id', flat=True)
            if building_id:
                # If building_id is provided, check if union_head manages that building
                if building_id in [str(bid) for bid in building_ids]:
                    queryset = queryset.filter(packagebuilding__building_id=building_id).distinct()
                else:
                    queryset = Package.objects.none()
            else:
                queryset = queryset.filter(packagebuilding__building_id__in=building_ids).distinct()

        else:
            # Admin or other roles → show all, or filter by building_id if provided
            if building_id:
                queryset = queryset.filter(packagebuilding__building_id=building_id).distinct()

        return queryset

    def perform_create(self, serializer):
        user = self.request.user

        # Get roles from database
        roles = [ur.role.name for ur in user.userrole_set.all()]

        # Add implied roles based on profiles
        from apps.accounts.models import ResidentProfile
        from apps.buildings.models import Building
        is_resident = ResidentProfile.objects.filter(user=user).exists()
        is_union_head = Building.objects.filter(union_head=user).exists()

        if is_resident and 'resident' not in roles:
            roles.append('resident')
        if is_union_head and 'union_head' not in roles:
            roles.append('union_head')

        package = serializer.save(created_by=user)

        # Staff/Admins behave like Union Heads
        if 'union_head' in roles or user.is_staff or user.is_superuser:
            from rest_framework.exceptions import ValidationError
            buildings = self.request.data.get('buildings', [])
            if not buildings:
                raise ValidationError("Union head must specify at least one building when creating a package.")

            for building_id in buildings:
                PackageBuilding.objects.create(package=package, building_id=building_id)

            self._send_package_notification(package, action="created")

        elif 'resident' in roles:
            from apps.accounts.models import ResidentProfile
            from rest_framework.exceptions import ValidationError
            from .models import PackageInvoice

            try:
                # Use filter().first() to avoid crash on multiple profiles, though it should be unique
                resident_profile = ResidentProfile.objects.filter(user=user).first()
                if not resident_profile or not resident_profile.unit or not resident_profile.unit.building:
                     raise ValidationError("Your resident profile is incomplete or missing a building assignment.")
                building = resident_profile.unit.building
            except Exception as e:
                raise ValidationError(f"Could not resolve resident profile: {e}")
            
            package.refresh_from_db()
            amount = 0
            due_date = package.start_date

            if hasattr(package, 'packageutility'):
                amount = package.packageutility.monthly_amount
            elif hasattr(package, 'packageprepaid'):
                amount = package.packageprepaid.average_monthly_charge
            elif hasattr(package, 'packagefixed'):
                amount = package.packagefixed.monthly_amount
            elif hasattr(package, 'packagemisc'):
                amount = package.packagemisc.total_amount
                due_date = package.packagemisc.deadline

            if not amount or amount <= 0:
                raise ValidationError("Could not determine a valid, positive amount for the package invoice.")

            PackageInvoice.objects.create(
                package=package,
                building=building,
                resident=resident_profile,
                amount=amount,
                due_date=due_date,
            )
            
            from apps.notifications.models import Notification
            Notification.objects.create(
                user=user,
                title="Personal Package Created",
                message=f"Your personal package '{package.name}' has been successfully created and an invoice has been issued."
            )
        
        return package

    def perform_update(self, serializer):
        package = serializer.save()

        # إرسال إشعارات لسكان العمارات عند التعديل
        self._send_package_notification(package, action="updated")
        return package

    def perform_destroy(self, instance):
        # إرسال إشعارات لسكان العمارات قبل الحذف
        self._send_package_notification(instance, action="deleted")

        # حذف الباقة
        instance.delete()

    def _send_package_notification(self, package, action="created"):
        """إرسال إشعار لسكان العمارات ورئيس الاتحاد عند إضافة/تعديل/حذف باقة"""
        from apps.notifications.models import Notification
        from apps.accounts.models import ResidentProfile

        # الحصول على سكان العمارات المرتبطة
        package_buildings = PackageBuilding.objects.filter(package=package)
        residents = ResidentProfile.objects.filter(unit__building__in=[pb.building for pb in package_buildings])

        # تحديد الرسائل حسب الإجراء
        if action == "created":
            resident_title = "باقة جديدة تم إضافتها"
            resident_message = f"تم إضافة باقة '{package.name}' إلى عمارتكم '{residents.first().building.name if residents else ''}'. يرجى مراجعة التفاصيل والدفع في الموعد المحدد."
            union_head_message = f"تم إضافة باقة '{package.name}' بنجاح."
        elif action == "updated":
            resident_title = "باقة تم تعديلها"
            resident_message = f"تم تعديل باقة '{package.name}' في عمارتكم '{residents.first().building.name if residents else ''}'. يرجى مراجعة التفاصيل الجديدة."
            union_head_message = f"تم تعديل باقة '{package.name}' بنجاح."
        elif action == "deleted":
            resident_title = "باقة تم حذفها"
            resident_message = f"تم حذف باقة '{package.name}' من عمارتكم '{residents.first().building.name if residents else ''}'."
            union_head_message = f"تم حذف باقة '{package.name}' بنجاح."
        else:
            return

        # إنشاء إشعارات لكل ساكن
        notifications = []
        for resident in residents:
            notifications.append(Notification(
                user=resident.user,
                title=resident_title,
                message=resident_message,
            ))

        # إرسال إشعار لرئيس الاتحاد
        union_heads = set()
        for pb in package_buildings:
            if pb.building.union_head:
                union_heads.add(pb.building.union_head)

        for union_head in union_heads:
            notifications.append(Notification(
                user=union_head,
                title=resident_title,
                message=union_head_message,
            ))

        # حفظ الإشعارات دفعة واحدة
        Notification.objects.bulk_create(notifications)

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def generate_invoices(self, request):
        """
        Trigger manual generation of monthly invoices
        (useful for testing before cron/Celery runs automatically)
        """
        generate_monthly_invoices.delay()
        return Response({"message": "تم إطلاق عملية توليد الفواتير الشهرية"}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def invoice_history(request):
    """
    🔹 عرض سجل الفواتير (مدفوعة / غير مدفوعة) للمستخدم الحالي
    """
    user = request.user
    invoices = PackageInvoice.objects.none()

    # Get roles from database
    roles = [ur.role.name for ur in user.userrole_set.all()]

    # Add implied roles based on profiles
    from apps.accounts.models import ResidentProfile
    from apps.buildings.models import Building
    is_resident = ResidentProfile.objects.filter(user=user).exists()
    is_union_head = Building.objects.filter(union_head=user).exists()

    if is_resident and 'resident' not in roles:
        roles.append('resident')
    if is_union_head and 'union_head' not in roles:
        roles.append('union_head')

    # لو المستخدم ساكن
    if 'resident' in roles:
        resident_profiles = user.resident_profiles.all()
        invoices = PackageInvoice.objects.filter(resident__in=resident_profiles).order_by('-created_at')

    # لو المستخدم رئيس اتحاد
    elif 'union_head' in roles:
        building_ids = user.buildings.values_list('id', flat=True)
        invoices = PackageInvoice.objects.filter(building_id__in=building_ids).order_by('-created_at')

    # Admin or other roles → show all (if needed)
    # else:
    #     invoices = PackageInvoice.objects.all().order_by('-created_at')

    from .serializers import PackageInvoiceSerializer
    serializer = PackageInvoiceSerializer(invoices, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def package_types(request):
    """
    Return available package types
    """
    types = [
        {'value': 'utilities', 'label': 'المرافق'},
        {'value': 'prepaid', 'label': 'مسبق الدفع'},
        {'value': 'fixed', 'label': 'ثابت'},
        {'value': 'misc', 'label': 'متنوع'},
    ]
    return Response(types)
