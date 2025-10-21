from rest_framework.permissions import BasePermission

class IsTechnician(BasePermission):
    def has_permission(self, request, view):
        return request.user.roles.filter(name='technician').exists()

class IsResident(BasePermission):
    def has_permission(self, request, view):
        return request.user.roles.filter(name='resident').exists()

class IsUnionHead(BasePermission):
    def has_permission(self, request, view):
        return request.user.roles.filter(name='union_head').exists()
