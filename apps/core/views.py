from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from apps.accounts.models import ResidentProfile
from apps.buildings.models import Building
from apps.packages.models import PackageBuilding, PackageInvoice, Package
from apps.payments.models import Transaction
from apps.notifications.models import Notification

User = get_user_model()


class PublicAPIView(APIView):
    """
    View base مفتوح بدون أي تحقق أو توكن
    """
    authentication_classes = []
    permission_classes = [AllowAny]

    def initial(self, request, *args, **kwargs):
        print("✅ PublicAPIView loaded — no authentication required")
        return super().initial(request, *args, **kwargs)

# TODO: replace with actual ViewSets for models in this app


# Added by bootstrap_mkani_api_enhancements.py
DEFAULT_FILTERS = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """
    Get dashboard statistics for union_head users
    """
    user = request.user

    # Check if user is union_head (either has role or owns buildings)
    has_union_head_role = 'union_head' in user.roles
    owns_buildings = Building.objects.filter(union_head=user).exists()

    if not (has_union_head_role or owns_buildings):
        return Response({"error": "Access denied. Union head role required."}, status=403)

    # Get buildings owned by this union_head
    buildings = Building.objects.filter(union_head=user)

    # Statistics
    total_buildings = buildings.count()
    total_residents = ResidentProfile.objects.filter(
        unit__building__in=buildings,
        status='accepted'
    ).count()

    # Total packages (unique packages linked to buildings)
    total_packages = PackageBuilding.objects.filter(
        building__in=buildings
    ).values('package').distinct().count()

    # Monthly revenue (transactions in current month)
    current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    next_month = current_month + timedelta(days=32)
    next_month = next_month.replace(day=1)

    monthly_revenue = Transaction.objects.filter(
        wallet__owner_type='building',
        wallet__owner_id__in=buildings.values_list('id', flat=True),
        created_at__gte=current_month,
        created_at__lt=next_month,
        status='completed'
    ).aggregate(total=Sum('amount'))['total'] or 0

    # Pending maintenance requests - temporarily set to 0 since maintenance app is removed
    pending_maintenance = 0

    return Response({
        'totalBuildings': total_buildings,
        'totalResidents': total_residents,
        'totalPackages': total_packages,
        'monthlyRevenue': float(monthly_revenue),
        'pendingMaintenance': pending_maintenance
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def latest_activities(request):
    """
    Get latest activities for union_head users
    """
    user = request.user

    # Check if user is union_head (either has role or owns buildings)
    has_union_head_role = 'union_head' in user.roles
    owns_buildings = Building.objects.filter(union_head=user).exists()

    if not (has_union_head_role or owns_buildings):
        return Response({"error": "Access denied. Union head role required."}, status=403)

    # Get buildings owned by this union_head
    buildings = Building.objects.filter(union_head=user)
    building_ids = buildings.values_list('id', flat=True)

    activities = []

    # Recent transactions (payments)
    recent_transactions = Transaction.objects.filter(
        wallet__owner_type='building',
        wallet__owner_id__in=building_ids,
        status='completed'
    ).select_related('wallet', 'invoice').order_by('-created_at')[:5]

    for transaction in recent_transactions:
        building = buildings.filter(id=transaction.wallet.owner_id).first()
        activities.append({
            'id': f'transaction_{transaction.id}',
            'type': 'payment',
            'title': f'تم دفع فاتورة - {building.name if building else "عمارة"}',
            'description': f'مبلغ: {transaction.amount} ج.م',
            'timestamp': transaction.created_at,
            'icon': 'FaCheckCircle',
            'color': 'green'
        })

    # Maintenance requests removed - no activities to add

    # Recent resident registrations
    recent_residents = ResidentProfile.objects.filter(
        unit__building__in=buildings,
        status='accepted'
    ).select_related('unit__building', 'user').order_by('-created_at')[:3]

    for resident in recent_residents:
        activities.append({
            'id': f'resident_{resident.id}',
            'type': 'resident',
            'title': f'انضمام ساكن جديد - {resident.unit.building.name}',
            'description': f'{resident.user.full_name}',
            'timestamp': resident.created_at,
            'icon': 'FaUsers',
            'color': 'blue'
        })

    # Unread notifications count
    unread_notifications_count = Notification.objects.filter(
        user=user,
        is_read=False
    ).count()

    if unread_notifications_count > 0:
        activities.append({
            'id': 'unread_notifications',
            'type': 'notification',
            'title': f'إشعارات جديدة ({unread_notifications_count})',
            'description': f'لديك {unread_notifications_count} إشعار غير مقروء',
            'timestamp': Notification.objects.filter(user=user).order_by('-created_at').first().created_at if unread_notifications_count > 0 else timezone.now(),
            'icon': 'FaBell',
            'color': 'purple'
        })

    # Recent package additions
    recent_packages = Package.objects.filter(
        packagebuilding__building__in=buildings
    ).select_related('created_by').order_by('-created_at')[:3]

    for package in recent_packages:
        activities.append({
            'id': f'package_{package.id}',
            'type': 'package',
            'title': f'تم إضافة باقة جديدة - {package.name}',
            'description': package.description or f'باقة {package.get_package_type_display()}',
            'timestamp': package.created_at,
            'icon': 'FaBox',
            'color': 'blue'
        })

    # Sort all activities by timestamp and take top 10
    activities.sort(key=lambda x: x['timestamp'], reverse=True)
    activities = activities[:10]

    # Format timestamps as ISO strings for proper JavaScript parsing
    for activity in activities:
        activity['timestamp'] = activity['timestamp'].isoformat()

    return Response(activities)
