# Database Migration Issues - TODO

- [x] Fix import paths:
  - [x] Update permissions import in notifications app: Change 'from mkani.core.permissions import DynamicRolePermission' to 'from apps.core.permissions import DynamicRolePermission' in apps/notifications/views.py
- [x] Database setup:
  - [x] Run makemigrations
  - [x] Run migrate
