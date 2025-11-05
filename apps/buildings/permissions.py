from apps.core.permissions import DynamicRolePermission

class BuildingPermission(DynamicRolePermission):
    def has_permission(self, request, view):
        # Allow POST (create) for authenticated users on buildings endpoint
        if request.method == 'POST' and view.basename == 'building' and request.user.is_authenticated:
            return True
        # Otherwise, use the default DynamicRolePermission logic
        return super().has_permission(request, view)

# You can extend permissions here if needed per app
AppPermission = DynamicRolePermission
