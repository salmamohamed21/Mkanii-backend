from rest_framework import status, generics, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth import authenticate, get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import send_mail
import json
import logging
import random
from django.contrib.auth.hashers import make_password

from django.conf import settings

from ..models import User, ResidentProfile, TechnicianProfile, Role, PasswordResetCode
from ..serializers import (
    UserSerializer,
    ResidentProfileSerializer,
    TechnicianProfileSerializer,
)
from apps.buildings.models import Building
from apps.buildings.serializers import BuildingSerializer
from apps.payments.models import Wallet

User = get_user_model()
logger = logging.getLogger(__name__)


# ============================
# 🧩 تسجيل مستخدم جديد
# ============================
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        data = request.data.copy()

        # تحويل الأدوار إلى list من strings
        if 'roles' in data:
            try:
                roles_value = data['roles']
                if isinstance(roles_value, str):
                    roles_value = json.loads(roles_value)
                if not isinstance(roles_value, list):
                    roles_value = [roles_value]
                data['role_names'] = [str(r) for r in roles_value]
            except Exception:
                data['role_names'] = [str(data['roles'])]

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        role_names = data.get('role_names', [])
        logger.info(f"Received role_names: {role_names}")

        # --------------------------------------
        # 🏢 إذا كان المستخدم رئيس اتحاد (union_head)
        # --------------------------------------
        if 'union_head' in role_names:
            logger.info(f"Creating union_head profile for user {user.id}")
            required_fields = ['name', 'total_units', 'total_floors', 'units_per_floor']
            missing_fields = [field for field in required_fields if not data.get(field)]
            if missing_fields:
                return Response(
                    {"error": f"الحقول التالية مطلوبة لإنشاء العمارة: {', '.join(missing_fields)}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            address_parts = [
                data.get('province', ''),
                data.get('city', ''),
                data.get('district', ''),
                data.get('street', ''),
            ]
            address = ' '.join(part for part in address_parts if part).strip() or 'غير محدد'

            building = Building.objects.create(
                union_head=user,
                name=data.get('name'),
                address=address,
                total_units=data.get('total_units'),
                total_floors=data.get('total_floors'),
                units_per_floor=data.get('units_per_floor'),
                subscription_plan=data.get('subscription_plan', 'basic'),
            )

            # إنشاء محفظة لرئيس الاتحاد
            Wallet.objects.create(owner_type='union_head', owner_id=user.id, current_balance=0)

            # إنشاء محفظة للعمارة
            Wallet.objects.create(owner_type='building', owner_id=building.id, current_balance=0)

        # --------------------------------------
        # 🏠 إذا كان المستخدم ساكن (resident)
        # --------------------------------------
        if 'resident' in role_names:
            logger.info(f"Creating resident profile for user {user.id}")
            ResidentProfile.objects.create(
                user=user,
                building_id=data.get('building_id') if data.get('building_id') else None,
                floor_number=data.get('floor_number'),
                apartment_number=data.get('apartment_number'),
                resident_type=data.get('resident_type', 'owner'),
                owner_national_id=data.get('owner_national_id') if data.get('resident_type') == 'tenant' else None,
                manual_building_name=data.get('manual_building_name'),
                manual_address=data.get('manual_address'),
            )

            # إنشاء محفظة للساكن
            Wallet.objects.create(owner_type='user', owner_id=user.id, current_balance=0)

        # --------------------------------------
        # 🔧 إذا كان المستخدم فني (technician)
        # --------------------------------------
        if 'technician' in role_names:
            logger.info(f"Creating technician profile for user {user.id}")
            TechnicianProfile.objects.create(
                user=user,
                specialization=data.get('specialization'),
                work_area=data.get('work_area'),
                employment_status=data.get('employment_status'),
                services_description=data.get('services_description', ''),
                rate=data.get('rate', 0),
            )

            # إنشاء محفظة للفني
            Wallet.objects.create(owner_type='user', owner_id=user.id, current_balance=0)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        user = authenticate(request, username=email, password=password)

        if not user:
            return Response({"detail": "بيانات الدخول غير صحيحة"}, status=400)

        refresh = RefreshToken.for_user(user)
        response = Response({"message": "تم تسجيل الدخول بنجاح"})

        # تخزين التوكينات داخل الكوكيز
        response.set_cookie("access_token", str(refresh.access_token), httponly=True, samesite="None", secure=True)
        response.set_cookie("refresh_token", str(refresh), httponly=True, samesite="None", secure=True)
        return response





class LogoutView(APIView):
    def post(self, request):
        response = Response({"message": "تم تسجيل الخروج"})
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        return response


# ============================
# 🔹 PASSWORD RESET
# ============================
class PasswordResetView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "هذا البريد غير مسجل"}, status=400)

        # توليد كود 6 أرقام
        code = str(random.randint(100000, 999999))
        PasswordResetCode.objects.create(user=user, code=code)

        send_mail(
            subject="رمز استعادة كلمة المرور",
            message=f"رمز التحقق الخاص بك هو: {code}",
            from_email="noreply@yourapp.com",
            recipient_list=[email],
        )
        return Response({"message": "تم إرسال الرمز إلى بريدك الإلكتروني."})


# ============================
# 🔹 PASSWORD RESET CONFIRM
# ============================
class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        code = request.data.get("code")
        new_password = request.data.get("new_password")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "المستخدم غير موجود."}, status=404)

        # البحث عن كود صالح
        reset_code = PasswordResetCode.objects.filter(
            user=user,
            code=code,
            is_used=False
        ).first()

        if not reset_code or not reset_code.is_valid():
            return Response({"error": "كود التحقق غير صحيح أو منتهي الصلاحية."}, status=400)

        # تحديث كلمة المرور
        user.set_password(new_password)
        user.save()

        # تحديث الكود كمستخدم
        reset_code.is_used = True
        reset_code.save()

        return Response({"message": "تم إعادة تعيين كلمة المرور بنجاح."})


# ============================
# 🔹 PASSWORD CHANGE
# ============================
class PasswordChangeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")

        if not user.check_password(old_password):
            return Response({"error": "كلمة المرور القديمة غير صحيحة"}, status=400)

        user.set_password(new_password)
        user.save()
        return Response({"message": "تم تغيير كلمة المرور بنجاح"})


# ============================
# 🔹 USER ROLES
# ============================
class UserRolesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"roles": request.user.roles})


# ============================
# 🔹 ADD ROLE
# ============================
class AddRoleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        new_role = request.data.get("role")
        user = request.user
        if new_role not in user.roles:
            user.roles.append(new_role)
            user.save()
            return Response({"message": f"تمت إضافة الدور '{new_role}' بنجاح."})
        return Response({"message": "الدور موجود بالفعل."})


# 👤 عرض البروفايل
class ProfileView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


# 👤 تحديث البروفايل
class UpdateProfileView(generics.UpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


# 🏢 إدارة بروفايلات الأدوار
class BuildingViewSet(viewsets.ModelViewSet):
    queryset = Building.objects.all()
    serializer_class = BuildingSerializer
    permission_classes = [IsAuthenticated]


class ResidentProfileViewSet(viewsets.ModelViewSet):
    queryset = ResidentProfile.objects.all()
    serializer_class = ResidentProfileSerializer
    permission_classes = [IsAuthenticated]


class TechnicianProfileViewSet(viewsets.ModelViewSet):
    queryset = TechnicianProfile.objects.all()
    serializer_class = TechnicianProfileSerializer
    permission_classes = [IsAuthenticated]


# ============================
# 🔹 SEARCH BY NATIONAL ID
# ============================
@api_view(['GET'])
@permission_classes([AllowAny])
def search_by_national_id(request, national_id):
    try:
        user = User.objects.get(national_id=national_id)
        return Response({
            "id": user.id,
            "full_name": user.full_name,
            "phone_number": user.phone_number
        })
    except User.DoesNotExist:
        return Response({"detail": "User not found"}, status=404)


# ============================
# 🔹 RESIDENT PROFILE DATA
# ============================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_resident_profile_data(request):
    try:
        resident_profile = ResidentProfile.objects.get(user=request.user)
        from apps.packages.models import Package, PackageBuilding, PackageInvoice

        # الباقات المشتركة (من العمارة)
        building_packages = []
        if resident_profile.building:
            package_buildings = PackageBuilding.objects.filter(building=resident_profile.building)
            for pb in package_buildings:
                package_invoices = PackageInvoice.objects.filter(
                    package=pb.package,
                    resident=resident_profile,
                    status__in=['pending', 'paid']
                )
                if package_invoices.exists():
                    building_packages.append({
                        'id': pb.package.id,
                        'name': pb.package.name,
                        'type': 'building',
                        'status': package_invoices.first().status,
                        'amount': package_invoices.first().amount,
                        'due_date': package_invoices.first().due_date,
                        'description': pb.package.description,
                        'is_recurring': pb.package.is_recurring,
                    })

        # الباقات الخاصة (التي أنشأها الساكن)
        personal_packages = []
        user_packages = Package.objects.filter(created_by=request.user)
        for pkg in user_packages:
            package_invoices = PackageInvoice.objects.filter(
                package=pkg,
                resident=resident_profile,
                status__in=['pending', 'paid']
            )
            if package_invoices.exists():
                personal_packages.append({
                    'id': pkg.id,
                    'name': pkg.name,
                    'type': 'personal',
                    'status': package_invoices.first().status,
                    'amount': package_invoices.first().amount,
                    'due_date': package_invoices.first().due_date,
                    'description': pkg.description,
                    'is_recurring': pkg.is_recurring,
                })

        return Response({
            'building_name': resident_profile.building.name if resident_profile.building else resident_profile.manual_building_name,
            'address': resident_profile.building.address if resident_profile.building else resident_profile.manual_address,
            'floor_number': resident_profile.floor_number,
            'apartment_number': resident_profile.apartment_number,
            'resident_type': resident_profile.resident_type,
            'building_packages': building_packages,
            'personal_packages': personal_packages,
        })
    except ResidentProfile.DoesNotExist:
        return Response({"detail": "Resident profile not found"}, status=404)


# ============================
# 🔹 TECHNICIAN PROFILE DATA
# ============================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_technician_profile_data(request):
    try:
        technician_profile = TechnicianProfile.objects.get(user=request.user)
        return Response({
            'specialization': technician_profile.specialization,
            'work_area': technician_profile.work_area,
            'employment_status': technician_profile.employment_status,
            'services_description': technician_profile.services_description,
            'rate': technician_profile.rate,
        })
    except TechnicianProfile.DoesNotExist:
        return Response({"detail": "Technician profile not found"}, status=404)


# ============================
# 🔹 UNION HEAD PROFILE DATA
# ============================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_union_head_profile_data(request):
    try:
        from apps.packages.models import Package, PackageBuilding, PackageInvoice

        # الحصول على العمارات الخاصة برئيس الاتحاد
        user_buildings = Building.objects.filter(union_head=request.user)

        buildings_data = []
        for building in user_buildings:
            # الباقات المرتبطة بالعمارة
            building_packages = Package.objects.filter(packagebuilding__building=building).only('id', 'name', 'description', 'is_recurring', 'package_type', 'created_at')

            packages_data = []
            for pkg in building_packages:
                # الحصول على حالة الدفع من الفواتير
                package_invoices = PackageInvoice.objects.filter(package=pkg, building=building).order_by('-created_at')
                status = 'active'  # افتراضي
                amount = 0
                due_date = None
                if package_invoices.exists():
                    latest_invoice = package_invoices.first()
                    status = latest_invoice.status
                    amount = latest_invoice.amount
                    due_date = latest_invoice.due_date

                packages_data.append({
                    'id': pkg.id,
                    'name': pkg.name,
                    'status': status,
                    'amount': amount,
                    'due_date': due_date,
                    'description': pkg.description,
                    'is_recurring': pkg.is_recurring,
                    'package_type': pkg.package_type,
                    'created_at': pkg.created_at,
                })

            buildings_data.append({
                'id': building.id,
                'name': building.name,
                'address': building.address,
                'total_units': building.total_units,
                'total_floors': building.total_floors,
                'units_per_floor': building.units_per_floor,
                'packages': packages_data,
            })

        # الباقات التي أنشأها رئيس الاتحاد شخصياً (غير مرتبطة بعمارة محددة)
        created_packages = Package.objects.filter(created_by=request.user).exclude(packagebuilding__building__in=user_buildings).only('id', 'name', 'description', 'is_recurring', 'package_type', 'created_at')

        personal_packages_data = []
        for pkg in created_packages:
            package_invoices = PackageInvoice.objects.filter(package=pkg).order_by('-created_at')
            status = 'active'
            amount = 0
            due_date = None
            if package_invoices.exists():
                latest_invoice = package_invoices.first()
                status = latest_invoice.status
                amount = latest_invoice.amount
                due_date = latest_invoice.due_date

            personal_packages_data.append({
                'id': pkg.id,
                'name': pkg.name,
                'status': status,
                'amount': amount,
                'due_date': due_date,
                'description': pkg.description,
                'is_recurring': pkg.is_recurring,
                'package_type': pkg.package_type,
                'created_at': pkg.created_at,
            })

        return Response({
            'buildings': buildings_data,
            'personal_packages': personal_packages_data,
        })
    except Exception as e:
        return Response({"detail": f"Error fetching union head profile data: {str(e)}"}, status=500)
