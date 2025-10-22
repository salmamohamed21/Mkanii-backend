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

        roles = getattr(user, 'roles', None)
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

        # Allow authenticated users to read and update notifications since queryset is filtered by user
        if view.basename == "notification" and request.method in ["GET", "POST"] and user.is_authenticated:
            return True

        if "resident" in flattened_roles:
            return view.action in ["list", "retrieve", "create"]
        elif "technician" in flattened_roles:
            return view.basename in ["maintenance", "notification"]
        elif "union_head" in flattened_roles:
            return True
        return False

    def has_object_permission(self, request, view, obj):
        user = request.user

        if user.is_superuser or user.is_staff:
            return True

        roles = getattr(user, 'roles', None)
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

        if "resident" in flattened_roles and hasattr(obj, "resident"):
            return obj.resident.user == user

        if "technician" in flattened_roles and hasattr(obj, "assigned_to"):
            return obj.assigned_to == user

        if "union_head" in flattened_roles:
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
