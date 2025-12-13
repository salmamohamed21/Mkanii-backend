from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import Unit, Building
from .serializers import UnitSerializer

class AvailableUnitsListView(APIView):
    """
    Get available units for a specific building.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, building_id):
        try:
            building = Building.objects.get(id=building_id)
        except Building.DoesNotExist:
            return Response({'error': 'Building not found'}, status=404)

        units = Unit.objects.filter(building=building, status='available')
        serializer = UnitSerializer(units, many=True)
        return Response(serializer.data)
