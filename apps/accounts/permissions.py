from rest_framework.permissions import BasePermission

class IsUnionHead(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and 'union_head' in getattr(request.user, 'roles', [])

class IsResident(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and 'resident' in getattr(request.user, 'roles', [])

class IsTechnician(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and 'technician' in getattr(request.user, 'roles', [])
