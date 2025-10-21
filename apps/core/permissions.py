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

        role = getattr(user, "role", None)

        if role == "resident":
            return view.action in ["list", "retrieve", "create"]
        elif role == "technician":
            return getattr(view, "basename", "") == "maintenancerequest"
        elif role == "union_head":
            return True
        return False

    def has_object_permission(self, request, view, obj):
        user = request.user
        role = getattr(user, "role", None)

        if user.is_superuser or user.is_staff:
            return True

        if role == "resident" and hasattr(obj, "resident"):
            return obj.resident.user == user

        if role == "technician" and hasattr(obj, "assigned_to"):
            return obj.assigned_to == user

        if role == "union_head" and hasattr(obj, "building"):
            return obj.building.union_head == user

        return False

# Legacy permission classes for backward compatibility
class IsUnionHead(permissions.BasePermission):
    def has_permission(self, request, view):
        return getattr(request.user, 'role', None) == 'union_head'

class IsResident(permissions.BasePermission):
    def has_permission(self, request, view):
        return getattr(request.user, 'role', None) == 'resident'

class IsTechnician(permissions.BasePermission):
    def has_permission(self, request, view):
        return getattr(request.user, 'role', None) == 'technician'
