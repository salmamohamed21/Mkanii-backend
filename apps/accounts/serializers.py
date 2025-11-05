from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.validators import MinLengthValidator, RegexValidator
from django.core.exceptions import ValidationError
from .models import ResidentProfile, Role
from apps.buildings.models import Building
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


# 🔹 حقل مساعد للتعامل مع القوائم النصية
class StringListField(serializers.ListField):
    child = serializers.CharField()

    def to_internal_value(self, data):
        if not isinstance(data, list):
            self.fail('not_a_list', input_type=type(data).__name__)
        return [str(item) for item in data]


# 🔹 User Serializer
class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        validators=[
            MinLengthValidator(8, message="كلمة المرور يجب أن تكون على الأقل 8 أحرف."),
            RegexValidator(
                regex=r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]',
                message="كلمة المرور يجب أن تحتوي على حرف كبير، حرف صغير، رقم، ورمز خاص."
            )
        ]
    )
    roles = serializers.SerializerMethodField(read_only=True)
    role_names = StringListField(write_only=True, required=False)

    class Meta:
        model = User
        fields = [
            "id", "email", "username", "full_name", "phone_number",
            "national_id", "date_of_birth", "roles", "role_names", "password"
        ]
        read_only_fields = ["id", "username"]

    def create(self, validated_data):
        # استخراج الأدوار (قائمة أسماء)
        role_names = validated_data.pop('role_names', [])
        logger.info(f"Role names in serializer: {role_names}")
        validated_data['username'] = validated_data.get('email')
        password = validated_data.pop("password", None)

        user = User(**validated_data)
        if password:
            user.set_password(password)
        user.save()

        # إنشاء الأدوار إذا لم تكن موجودة وربطها
        roles = []
        for role_name in role_names:
            role, created = Role.objects.get_or_create(name=role_name)
            roles.append(role)
            if created:
                logger.info(f"Created new role: {role_name}")
        # Use userrole_set to set roles
        user.userrole_set.all().delete()  # Clear existing roles
        for role in roles:
            user.userrole_set.create(role=role)
        logger.info(f"Assigned roles to user {user.id}: {[r.name for r in roles]}")
        # Verify roles are set
        assigned = [ur.role for ur in user.userrole_set.all()]
        logger.info(f"Verified assigned roles: {[r.name for r in assigned]}")
        return user

    def get_roles(self, obj):
        # Get roles from userrole_set
        assigned_roles = [ur.role.name for ur in obj.userrole_set.all()]

        # Check for implied roles based on profiles
        if ResidentProfile.objects.filter(user=obj).exists():
            if 'resident' not in assigned_roles:
                assigned_roles.append('resident')
        if Building.objects.filter(union_head=obj).exists():
            if 'union_head' not in assigned_roles:
                assigned_roles.append('union_head')

        return assigned_roles





class ResidentProfileSerializer(serializers.ModelSerializer):
    building_name = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()
    unit_details = serializers.SerializerMethodField()

    class Meta:
        model = ResidentProfile
        fields = "__all__"

    def get_building_name(self, obj):
        if obj.building:
            return obj.building.name
        return obj.manual_building_name

    def get_address(self, obj):
        if obj.building:
            return obj.building.address
        return obj.manual_address

    def get_unit_details(self, obj):
        if obj.unit:
            return {
                'id': obj.unit.id,
                'floor_number': obj.unit.floor_number,
                'apartment_number': obj.unit.apartment_number,
                'area': obj.unit.area,
                'rooms_count': obj.unit.rooms_count,
                'status': obj.unit.status,
            }
        return None



