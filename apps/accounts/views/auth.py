from rest_framework import status, generics, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import api_view, permission_classes, action
from django.contrib.auth import authenticate, get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import send_mail
import json
import logging
import random
from django.contrib.auth.hashers import make_password

from django.conf import settings

from ..models import User, ResidentProfile, Role, PasswordResetCode
from ..serializers import (
    UserSerializer,
    ResidentProfileSerializer,
)
from apps.buildings.models import Building, Unit
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
        # استخراج البيانات من FormData
        data = {}
        for key, value in request.data.items():
            if hasattr(value, 'read'):  # ملف
                data[key] = value
            else:
                data[key] = value

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
            resident_type = data.get('resident_type', 'owner')
            floor_number = data.get('floor_number')
            apartment_number = data.get('apartment_number')
            building_id = data.get('building_id')
            building_name = data.get('building_name')
            address = data.get('address')

            # التحقق من الحقول المطلوبة حسب نوع الساكن
            if resident_type == 'owner':
                # 'area' and 'rooms_count' are optional for owners, save if provided
                pass
            elif resident_type == 'tenant':
                required_fields = ['owner_national_id', 'rental_start_date', 'rental_end_date', 'rental_value']
                missing_fields = [field for field in required_fields if not data.get(field)]
                if missing_fields:
                    return Response(
                        {"error": f"الحقول التالية مطلوبة للمستأجر: {', '.join(missing_fields)}"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            # إنشاء أو الحصول على العمارة إذا لم يكن building_id موجوداً
            building = None
            if building_id:
                try:
                    building = Building.objects.get(id=building_id)
                except Building.DoesNotExist:
                    return Response(
                        {"error": "العمارة المحددة غير موجودة"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            elif building_name and address:
                # إنشاء عمارة جديدة إذا لم تكن موجودة
                building, created = Building.objects.get_or_create(
                    name=building_name,
                    address=address,
                    defaults={
                        'total_units': 1,  # قيمة افتراضية
                        'total_floors': 1,
                        'units_per_floor': 1,
                        'subscription_plan': 'basic',
                    }
                )

            # إنشاء أو الحصول على الوحدة
            unit = None
            if building and floor_number and apartment_number:
                unit, created = Unit.objects.get_or_create(
                    building=building,
                    floor_number=floor_number,
                    apartment_number=apartment_number,
                    defaults={
                        'area': data.get('area') if resident_type == 'owner' else None,
                        'rooms_count': data.get('rooms_count') if resident_type == 'owner' else None,
                        'status': 'available',
                    }
                )
                # تحديث البيانات إذا كانت موجودة
                if resident_type == 'owner':
                    unit.area = data.get('area')
                    unit.rooms_count = data.get('rooms_count')
                    unit.save()

            # إنشاء ResidentProfile
            resident_profile_data = {
                'user': user,
                'unit': unit,
                'resident_type': resident_type,
                'status': 'active',
                'is_present': True,
            }

            # إضافة البيانات المشتركة
            if not unit:
                resident_profile_data.update({
                    'manual_building_name': building_name,
                    'manual_address': address,
                    'floor_number': floor_number,
                    'apartment_number': apartment_number,
                })

            if resident_type == 'owner':
                # إضافة area و rooms_count للمالك
                resident_profile_data.update({
                    'area': data.get('area'),
                    'rooms_count': data.get('rooms_count'),
                })
            elif resident_type == 'tenant':
                # البحث عن المالك باستخدام national_id
                owner_national_id = data.get('owner_national_id')
                try:
                    owner = User.objects.get(national_id=owner_national_id)
                    resident_profile_data['owner'] = owner
                except User.DoesNotExist:
                    return Response(
                        {"error": "الرقم الوطني للمالك غير صحيح أو غير موجود"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                resident_profile_data.update({
                    'rental_start_date': data.get('rental_start_date'),
                    'rental_end_date': data.get('rental_end_date'),
                    'rental_value': data.get('rental_value'),
                })

            ResidentProfile.objects.create(**resident_profile_data)

            # إنشاء محفظة للساكن
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
        # Get roles from database
        roles = [ur.role.name for ur in request.user.userrole_set.all()]

        # Add implied roles based on profiles
        from apps.accounts.models import ResidentProfile
        from apps.buildings.models import Building
        if ResidentProfile.objects.filter(user=request.user).exists():
            if 'resident' not in roles:
                roles.append('resident')
        if Building.objects.filter(union_head=request.user).exists():
            if 'union_head' not in roles:
                roles.append('union_head')

        return Response({"roles": roles})


# ============================
# 🔹 ADD ROLE
# ============================
class AddRoleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        new_role = request.data.get("role")
        user = request.user
        # Get current roles from database
        current_roles = [ur.role.name for ur in user.userrole_set.all()]
        if new_role not in current_roles:
            # Create the role if it doesn't exist
            role, created = Role.objects.get_or_create(name=new_role)
            user.userrole_set.create(role=role)
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

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def submit_rental_request(self, request):
        """
        Endpoint for tenant to submit rental request.
        Creates ResidentProfile as tenant with 'pending' status.
        """
        data = request.data.copy()
        data['user'] = request.user.id
        data['resident_type'] = 'tenant'
        data['status'] = 'pending'

        # Validate required fields
        required_fields = ['unit', 'rental_duration', 'rental_start_date', 'rental_value']
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return Response(
                {"error": f"الحقول التالية مطلوبة: {', '.join(missing_fields)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if unit exists and is available
        from apps.buildings.models import Unit
        try:
            unit = Unit.objects.get(id=data['unit'], status='available')
        except Unit.DoesNotExist:
            return Response(
                {"error": "الوحدة غير متوفرة أو غير موجودة"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if user already has a pending request for this unit
        existing_request = ResidentProfile.objects.filter(
            user=request.user,
            unit=unit,
            resident_type='tenant',
            status__in=['pending', 'approved']
        ).exists()
        if existing_request:
            return Response(
                {"error": "لديك طلب إيجار معلق أو معتمد بالفعل لهذه الوحدة"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        resident_profile = serializer.save()

        return Response({
            "message": "تم إرسال طلب الإيجار بنجاح",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def approve_rental_request(self, request, pk=None):
        """
        Endpoint for owner to approve tenant rental request.
        Updates tenant status to 'approved', sets unit.status='occupied'.
        """
        resident_profile = self.get_object()

        # Check if user is the owner of the unit
        if resident_profile.unit.building.union_head != request.user:
            return Response(
                {"error": "ليس لديك صلاحية الموافقة على هذا الطلب"},
                status=status.HTTP_403_FORBIDDEN
            )

        if resident_profile.resident_type != 'tenant' or resident_profile.status != 'pending':
            return Response(
                {"error": "هذا الطلب غير صالح للموافقة"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update resident profile status
        resident_profile.status = 'approved'
        resident_profile.is_present = True
        resident_profile.save()

        # Update unit status
        resident_profile.unit.status = 'occupied'
        resident_profile.unit.save()

        # Send notification to tenant
        from apps.notifications.models import Notification
        Notification.objects.create(
            user=resident_profile.user,
            title="تمت الموافقة على طلب الإيجار",
            message=f"تمت الموافقة على طلب إيجار الوحدة {resident_profile.unit.apartment_number} في العمارة {resident_profile.unit.building.name}"
        )

        return Response({
            "message": "تمت الموافقة على طلب الإيجار بنجاح"
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def reject_rental_request(self, request, pk=None):
        """
        Endpoint for owner to reject tenant rental request.
        """
        resident_profile = self.get_object()
        rejection_reason = request.data.get('rejection_reason', '')

        # Check if user is the owner of the unit
        if resident_profile.unit.building.union_head != request.user:
            return Response(
                {"error": "ليس لديك صلاحية رفض هذا الطلب"},
                status=status.HTTP_403_FORBIDDEN
            )

        if resident_profile.resident_type != 'tenant' or resident_profile.status != 'pending':
            return Response(
                {"error": "هذا الطلب غير صالح للرفض"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update resident profile status
        resident_profile.status = 'rejected'
        resident_profile.save()

        # Send notification to tenant
        from apps.notifications.models import Notification
        message = f"تم رفض طلب إيجار الوحدة {resident_profile.unit.apartment_number} في العمارة {resident_profile.unit.building.name}"
        if rejection_reason:
            message += f". السبب: {rejection_reason}"

        Notification.objects.create(
            user=resident_profile.user,
            title="تم رفض طلب الإيجار",
            message=message
        )

        return Response({
            "message": "تم رفض طلب الإيجار"
        }, status=status.HTTP_200_OK)





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
