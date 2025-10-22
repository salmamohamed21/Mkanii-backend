# Database Migration Issues - TODO

- [x] Fix import paths:
  - [x] Update permissions import in notifications app: Change 'from mkani.core.permissions import DynamicRolePermission' to 'from apps.core.permissions import DynamicRolePermission' in apps/notifications/views.py
  - [x] Update permissions import in payments app: Change 'from mkani.core.permissions import DynamicRolePermission' to 'from apps.core.permissions import DynamicRolePermission' in apps/payments/views.py and apps/payments/permissions.py
  - [x] Update permissions import in packages app: Change 'from mkani.core.permissions import DynamicRolePermission' to 'from apps.core.permissions import DynamicRolePermission' in apps/packages/permissions.py and apps/packages/views.py
  - [x] Update permissions import in notifications app: Change 'from mkani.core.permissions import DynamicRolePermission' to 'from apps.core.permissions import DynamicRolePermission' in apps/notifications/permissions.py
  - [x] Update permissions import in buildings app: Change 'from mkani.core.permissions import DynamicRolePermission' to 'from apps.core.permissions import DynamicRolePermission' in apps/buildings/permissions.py and apps/buildings/views.py
  - [x] Update model imports in core app: Change 'from mkani.apps.packages.models import PackageBuilding' and 'from mkani.apps.buildings.models import Building' to 'from apps.packages.models import PackageBuilding' and 'from apps.buildings.models import Building' in core/permissions.py
- [x] Database setup:
  - [x] Run makemigrations
  - [x] Run migrate
