from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Notification
from .serializers import NotificationSerializer
from mkani.core.permissions import DynamicRolePermission

class NotificationViewSet(viewsets.ModelViewSet):
    permission_classes = [DynamicRolePermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['title', 'created_at']
    search_fields = ['title', 'created_at']
    ordering_fields = ['title', 'created_at']

    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [DynamicRolePermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'created_at']
    ordering_fields = ['title', 'created_at']

    def get_queryset(self):
        user = self.request.user
        return Notification.objects.filter(user=user)

    @action(detail=False, methods=['get'], permission_classes=[DynamicRolePermission])
    def recent(self, request):
        qs = self.get_queryset().order_by('-id')[:10]
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        serializer = self.get_serializer(notification)
        return Response(serializer.data)

