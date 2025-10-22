from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import MaintenanceRequest
from .serializers import (
    MaintenanceRequestSerializer,
    CreateMaintenanceRequestSerializer,
)
from .permissions import IsResident, IsTechnician, IsUnionHead
from apps.notifications.models import Notification
from apps.accounts.models import TechnicianProfile, ResidentProfile

# ==========================================================
# 🔧 طلبات الصيانة
# ==========================================================
class MaintenanceRequestViewSet(viewsets.ModelViewSet):
    queryset = MaintenanceRequest.objects.all().order_by("-created_at")
    serializer_class = MaintenanceRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create_request":
            return CreateMaintenanceRequestSerializer
        return MaintenanceRequestSerializer

    # 🧱 1️⃣ الساكن يقدم طلب صيانة
    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated, IsResident])
    def create_request(self, request):
        serializer = CreateMaintenanceRequestSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            maintenance_request = serializer.save()

            # إرسال إشعار لرئيس الاتحاد
            union_head = maintenance_request.building.union_head
            Notification.objects.create(
                user=union_head,
                title="طلب صيانة جديد",
                message=f"تم تقديم طلب صيانة جديد من {request.user.full_name} للعمارة {maintenance_request.building.name}."
            )

            # إرسال إشعار للساكن نفسه لتأكيد الطلب
            Notification.objects.create(
                user=request.user,
                title="تم إرسال طلبك بنجاح",
                message=f"تم إرسال طلب الصيانة رقم #{maintenance_request.id} بنجاح، بانتظار التعيين لفني."
            )

            return Response(MaintenanceRequestSerializer(maintenance_request).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # 🧰 2️⃣ الفني يشوف الطلبات المخصصة له
    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated, IsTechnician])
    def assigned(self, request):
        from .models import TechnicianProfile
        technician = TechnicianProfile.objects.filter(user=request.user).first()
        if not technician:
            return Response({"error": "لم يتم العثور على ملف الفني."}, status=400)
        qs = MaintenanceRequest.objects.filter(technician=technician)
        serializer = MaintenanceRequestSerializer(qs, many=True)
        return Response(serializer.data)

    # ✅ 3️⃣ الفني يقبل أو يرفض الطلب
    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsTechnician])
    def update_status(self, request, pk=None):
        maintenance = get_object_or_404(MaintenanceRequest, pk=pk)
        new_status = request.data.get("status")

        if new_status not in ["in_progress", "completed", "rejected"]:
            return Response({"error": "الحالة غير صالحة."}, status=400)

        maintenance.status = new_status
        maintenance.save()

        # تحديد الساكن ورئيس الاتحاد
        building = maintenance.building
        union_head = building.union_head
        resident_user = None

        # نحاول ربط الطلب بالساكن في نفس المبنى
        resident_profile = ResidentProfile.objects.filter(building=building).first()
        if resident_profile:
            resident_user = resident_profile.user

        # إشعارات بناءً على الحالة
        if new_status == "in_progress":
            if resident_user:
                Notification.objects.create(
                    user=resident_user,
                    title="بدأت أعمال الصيانة",
                    message=f"بدأ الفني العمل على طلب الصيانة رقم #{maintenance.id}."
                )
            Notification.objects.create(
                user=union_head,
                title="طلب صيانة قيد التنفيذ",
                message=f"الفني بدأ في تنفيذ طلب الصيانة #{maintenance.id}."
            )

        if new_status == "completed":
            if resident_user:
                # خصم التكلفة من محفظة الساكن
                wallet = getattr(resident_user, "wallet", None)
                if wallet and wallet.balance >= maintenance.cost:
                    wallet.balance -= maintenance.cost
                    wallet.save()
                    Notification.objects.create(
                        user=resident_user,
                        title="تم إنهاء الصيانة",
                        message=f"تم إكمال طلب الصيانة رقم #{maintenance.id}. تم خصم {maintenance.cost} من محفظتك. شكرًا لتعاونك!"
                    )
                else:
                    # رصيد غير كافٍ
                    Notification.objects.create(
                        user=resident_user,
                        title="رصيد غير كافٍ",
                        message="رصيدك لا يكفي لإتمام طلب الصيانة رقم #{maintenance.id}."
                    )
                    # لا نغير الحالة إلى مكتملة إذا الرصيد غير كافٍ
                    return Response({"error": "رصيدك لا يكفي لإتمام الطلب."}, status=400)
            Notification.objects.create(
                user=union_head,
                title="تم إكمال طلب الصيانة",
                message=f"الفني أنهى العمل في طلب الصيانة #{maintenance.id}."
            )

        elif new_status == "rejected":
            Notification.objects.create(
                user=union_head,
                title="تم رفض الطلب",
                message=f"الفني رفض تنفيذ طلب الصيانة #{maintenance.id}."
            )

            if resident_user:
                Notification.objects.create(
                    user=resident_user,
                    title="تم رفض طلب الصيانة",
                    message=f"عذرًا، تم رفض طلب الصيانة رقم #{maintenance.id}."
                )

        return Response(MaintenanceRequestSerializer(maintenance).data)

    # 👁️ 4️⃣ رئيس الاتحاد يشوف كل الطلبات
    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated, IsUnionHead])
    def all_requests(self, request):
        buildings = request.user.owned_buildings.all()
        qs = MaintenanceRequest.objects.filter(building__in=buildings)
        serializer = MaintenanceRequestSerializer(qs, many=True)
        return Response(serializer.data)


# ==========================================================
# ⏰ جداول الفنيين
# ==========================================================
# TechnicianSchedule model removed, so this ViewSet is commented out
# class TechnicianScheduleViewSet(viewsets.ModelViewSet):
#     queryset = TechnicianSchedule.objects.all()
#     serializer_class = TechnicianScheduleSerializer
#     permission_classes = [IsAuthenticated, IsTechnician]

