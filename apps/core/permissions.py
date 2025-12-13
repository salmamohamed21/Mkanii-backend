from rest_framework import permissions
from apps.buildings.models import Building


def get_user_roles(user):
    """
    Get all roles for a user, including implied roles.
    """
    if not user or not user.is_authenticated:
        return []

    # Get roles from database
    roles = [ur.role.name for ur in user.userrole_set.all()]

    # Add implied roles based on profiles
    from apps.accounts.models import ResidentProfile
    is_resident = ResidentProfile.objects.filter(user=user).exists()
    is_union_head = Building.objects.filter(union_head=user).exists()

    if is_resident and 'resident' not in roles:
        roles.append('resident')
    if is_union_head and 'union_head' not in roles:
        roles.append('union_head')
    
    return roles


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

        roles = get_user_roles(user)

        if "union_head" in roles:
            return True
        
        if "resident" in roles:
            # Allow residents to access building list and detail
            if view.basename == 'building' and view.action in ['list', 'retrieve', 'resident_building']:
                return True
            # Allow residents to access their own data
            return view.action in ["list", "retrieve", "create"]

        if "technician" in roles:
            return getattr(view, "basename", "") == "maintenancerequest"

        return False

    def has_object_permission(self, request, view, obj):
        user = request.user

        if user.is_superuser or user.is_staff:
            return True

        roles = get_user_roles(user)
        
        if isinstance(obj, Building):
            if "union_head" in roles:
                return obj.union_head == user
            if "resident" in roles:
                # A resident can see details of their own building
                from apps.accounts.models import ResidentProfile
                return ResidentProfile.objects.filter(user=user, unit__building=obj).exists()
            return False

        if "resident" in roles and hasattr(obj, "user"):
            return obj.user == user
            
        if "resident" in roles and hasattr(obj, "resident"):
            return obj.resident.user == user

        if "technician" in roles and hasattr(obj, "assigned_to"):
            return obj.assigned_to == user

        if "union_head" in roles and hasattr(obj, "building"):
            return obj.building.union_head == user
        
        if "union_head" in roles and hasattr(obj, "unit"):
            if obj.unit.building.union_head == user:
                return True

        return False

# Legacy permission classes for backward compatibility
class IsUnionHead(permissions.BasePermission):
    def has_permission(self, request, view):
        return 'union_head' in get_user_roles(request.user)

class IsResident(permissions.BasePermission):
    def has_permission(self, request, view):
        return 'resident' in get_user_roles(request.user)

class IsTechnician(permissions.BasePermission):
    def has_permission(self, request, view):
        return 'technician' in get_user_roles(request.user)
