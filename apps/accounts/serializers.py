from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.validators import MinLengthValidator, RegexValidator
from django.core.exceptions import ValidationError
from .models import ResidentProfile, TechnicianProfile, TechnicianSchedule, Role
from mkani.apps.buildings.models import Building
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
        user.roles.set(roles)
        logger.info(f"Assigned roles to user {user.id}: {[r.name for r in roles]}")
        # Verify roles are set
        assigned = user.roles.all()
        logger.info(f"Verified assigned roles: {[r.name for r in assigned]}")
        return user

    def get_roles(self, obj):
        # Get roles from ManyToManyField
        assigned_roles = [role.name for role in obj.roles.all()]

        # Check for implied roles based on profiles
        if ResidentProfile.objects.filter(user=obj).exists():
            if 'resident' not in assigned_roles:
                assigned_roles.append('resident')
        if TechnicianProfile.objects.filter(user=obj).exists():
            if 'technician' not in assigned_roles:
                assigned_roles.append('technician')
        if Building.objects.filter(union_head=obj).exists():
            if 'union_head' not in assigned_roles:
                assigned_roles.append('union_head')

        return assigned_roles





class ResidentProfileSerializer(serializers.ModelSerializer):
    building_name = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()

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


class TechnicianProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TechnicianProfile
        fields = "__all__"


class TechnicianScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = TechnicianSchedule
        fields = "__all__"
