from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import MaintenanceRequestViewSet

router = DefaultRouter()
router.register(r"", MaintenanceRequestViewSet, basename="maintenance")

urlpatterns = [
    path("", include(router.urls)),
    path("technician-tasks/", MaintenanceRequestViewSet.as_view({"get": "assigned"}), name="technician-tasks"),
]
