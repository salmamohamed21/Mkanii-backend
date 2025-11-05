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

        # ✅ فلترة حسب building_id لو متبعت في الـ request
        building_id = self.request.query_params.get('building_id')
        if building_id:
            queryset = queryset.filter(packagebuilding__building_id=building_id).distinct()
            return queryset

        # ✅ باقي الفلترة حسب الدور
        if hasattr(user, 'roles') and 'resident' in user.roles:
            try:
                resident_profile = user.resident_profiles.first()
                if resident_profile and resident_profile.building:
                    queryset = queryset.filter(packagebuilding__building_id=resident_profile.building.id).distinct()
            except:
                queryset = Package.objects.none()

        elif hasattr(user, 'roles') and 'union_head' in user.roles:
            building_ids = user.buildings.values_list('id', flat=True)
            queryset = queryset.filter(packagebuilding__building_id__in=building_ids).distinct()

        # Admin or other roles → show all
        return queryset

    def perform_create(self, serializer):
        package = serializer.save(created_by=self.request.user)

        # Handle buildings association
        buildings = self.request.data.get('buildings', [])
        for building_id in buildings:
            PackageBuilding.objects.create(package=package, building_id=building_id)

        # إرسال إشعارات لسكان العمارات
        self._send_package_notification(package, action="created")
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
        residents = ResidentProfile.objects.filter(building__in=[pb.building for pb in package_buildings])

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

    # لو المستخدم ساكن
    if hasattr(user, 'roles') and 'resident' in user.roles:
        resident_profiles = user.resident_profiles.all()
        invoices = PackageInvoice.objects.filter(resident__in=resident_profiles).order_by('-created_at')

    # لو المستخدم رئيس اتحاد
    elif hasattr(user, 'roles') and 'union_head' in user.roles:
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
