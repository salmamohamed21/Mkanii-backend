from rest_framework import permissions

class DynamicRolePermission(permissions.BasePermission):
    '''
    Role-based dynamic permission:
    - Resident: limited to their own data
    - Technician: limited to assigned maintenance requests
    - UnionHead: full access to their building
    - Admin/Staff: full system access
    '''

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        if user.is_superuser or user.is_staff:
            return True

        # Get roles from database
        roles = [ur.role.name for ur in user.userrole_set.all()]

        # Add implied roles based on profiles
        from apps.accounts.models import ResidentProfile
        from apps.buildings.models import Building
        if ResidentProfile.objects.filter(user=user).exists():
            if 'resident' not in roles:
                roles.append('resident')
        if Building.objects.filter(union_head=user).exists():
            if 'union_head' not in roles:
                roles.append('union_head')

        # Allow authenticated users to read and update notifications since queryset is filtered by user
        if view.basename == "notification" and request.method in ["GET", "POST"] and user.is_authenticated:
            return True

        if "union_head" in roles:
            return True
        elif "technician" in roles:
            return view.basename in ["maintenance", "notification"]
        elif "resident" in roles:
            return view.action in ["list", "retrieve", "create"]
        return False

    def has_object_permission(self, request, view, obj):
        user = request.user

        if user.is_superuser or user.is_staff:
            return True

        # Get roles from database
        roles = [ur.role.name for ur in user.userrole_set.all()]

        # Add implied roles based on profiles
        from apps.accounts.models import ResidentProfile
        from apps.buildings.models import Building
        if ResidentProfile.objects.filter(user=user).exists():
            if 'resident' not in roles:
                roles.append('resident')
        if Building.objects.filter(union_head=user).exists():
            if 'union_head' not in roles:
                roles.append('union_head')

        if "resident" in roles and hasattr(obj, "resident"):
            return obj.resident.user == user

        if "technician" in roles and hasattr(obj, "assigned_to"):
            return obj.assigned_to == user

        if "union_head" in roles:
            if hasattr(obj, "union_head"):
                return obj.union_head == user
            # Special handling for Package model
            elif hasattr(obj, "_meta") and obj._meta.model_name == "package":
                # Check if user is union_head of any building associated with the package
                from apps.packages.models import PackageBuilding
                from apps.buildings.models import Building
                building_ids = PackageBuilding.objects.filter(package=obj).values_list('building_id', flat=True)
                return Building.objects.filter(id__in=building_ids, union_head=user).exists()

        return False
