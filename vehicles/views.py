from rest_framework.viewsets import ModelViewSet

from .models import Vehicle
from .permissions import VehiclePermission
from .serializers import VehicleSerializer


class VehicleViewSet(ModelViewSet):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    permission_classes = [VehiclePermission]