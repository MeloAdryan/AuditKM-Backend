from django.core.exceptions import ValidationError
from django.db.models import Sum

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from .models import (
    RouteAudit,
    StandardRoute,
    StandardRoutePoint,
    Trip,
)

from .permissions import TripPermission

from .serializers import (
    RouteAuditSerializer,
    StandardRoutePointSerializer,
    StandardRouteSerializer,
    TripLocationSerializer,
    TripSerializer,
)

from .services.route_audit import (
    generate_route_audit,
)


class StandardRouteViewSet(
    ModelViewSet
):
    serializer_class = (
        StandardRouteSerializer
    )

    permission_classes = [
        TripPermission,
    ]

    def get_queryset(self):
        user = self.request.user

        if not user.is_authenticated:
            return (
                StandardRoute.objects.none()
            )

        return (
            StandardRoute.objects
            .filter(
                active=True,
            )
            .prefetch_related(
                "points",
            )
            .order_by(
                "name",
            )
        )


class StandardRoutePointViewSet(
    ModelViewSet
):
    serializer_class = (
        StandardRoutePointSerializer
    )

    permission_classes = [
        IsAuthenticated,
    ]

    def get_queryset(self):
        queryset = (
            StandardRoutePoint.objects
            .select_related(
                "standard_route",
            )
            .order_by(
                "standard_route_id",
                "sequence",
            )
        )

        standard_route_id = (
            self.request
            .query_params
            .get(
                "standard_route"
            )
        )

        if standard_route_id:
            queryset = (
                queryset.filter(
                    standard_route_id=(
                        standard_route_id
                    )
                )
            )

        return queryset


class TripViewSet(
    ModelViewSet
):
    serializer_class = TripSerializer

    permission_classes = [
        TripPermission,
    ]

    def get_queryset(self):
        user = self.request.user

        queryset = (
            Trip.objects
            .select_related(
                "driver",
                "vehicle",
                "standard_route",
            )
            .all()
        )

        if not user.is_authenticated:
            return queryset.none()

        if user.is_superuser:
            return queryset

        role = getattr(
            user,
            "role",
            None,
        )

        if not role:
            return queryset.none()

        if role.name == "Motorista":
            return queryset.filter(
                driver=user,
            )

        return queryset

    def perform_create(
        self,
        serializer,
    ):
        user = self.request.user

        role = getattr(
            user,
            "role",
            None,
        )

        if (
            not user.is_superuser
            and role
            and role.name == "Motorista"
        ):
            serializer.save(
                driver=user,
            )

            return

        serializer.save()

    @action(
        detail=True,
        methods=[
            "get",
            "post",
        ],
        url_path="audit",
    )
    def audit(
        self,
        request,
        pk=None,
    ):
        trip = self.get_object()

        if request.method == "GET":
            try:
                audit = trip.route_audit

            except RouteAudit.DoesNotExist:
                return Response(
                    {
                        "detail": (
                            "Esta viagem ainda "
                            "não possui auditoria."
                        )
                    },
                    status=(
                        status
                        .HTTP_404_NOT_FOUND
                    ),
                )

            serializer = (
                RouteAuditSerializer(
                    audit,
                )
            )

            return Response(
                serializer.data,
                status=(
                    status.HTTP_200_OK
                ),
            )

        try:
            audit = generate_route_audit(
                trip,
            )

        except ValidationError as exc:
            if hasattr(
                exc,
                "message_dict",
            ):
                data = (
                    exc.message_dict
                )
            else:
                data = {
                    "detail":
                        exc.messages,
                }

            return Response(
                data,
                status=(
                    status
                    .HTTP_400_BAD_REQUEST
                ),
            )

        serializer = (
            RouteAuditSerializer(
                audit,
            )
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=[
            "get",
            "post",
        ],
        url_path="locations",
    )
    def locations(
        self,
        request,
        pk=None,
    ):
        trip = self.get_object()

        if request.method == "GET":
            locations = (
                trip.locations
                .all()
                .order_by(
                    "recorded_at",
                    "id",
                )
            )

            serializer = (
                TripLocationSerializer(
                    locations,
                    many=True,
                )
            )

            return Response(
                serializer.data,
                status=(
                    status.HTTP_200_OK
                ),
            )

        serializer = (
            TripLocationSerializer(
                data=request.data,
                context={
                    "trip": trip,
                },
            )
        )

        serializer.is_valid(
            raise_exception=True,
        )

        serializer.save()

        return Response(
            serializer.data,
            status=(
                status.HTTP_201_CREATED
            ),
        )


class DashboardView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    allowed_roles = {
        "Administrador",
        "Gestor",
        "Diretor",
    }

    def get(
        self,
        request,
    ):
        user = request.user

        role = getattr(
            user,
            "role",
            None,
        )

        role_name = (
            role.name
            if role
            else None
        )

        if (
            not user.is_superuser
            and role_name
            not in self.allowed_roles
        ):
            return Response(
                {
                    "detail": (
                        "Você não possui "
                        "permissão para "
                        "acessar o dashboard "
                        "gerencial."
                    )
                },
                status=(
                    status
                    .HTTP_403_FORBIDDEN
                ),
            )

        audits = (
            RouteAudit.objects
            .select_related(
                "trip",
                "trip__driver",
                "trip__vehicle",
                "standard_route",
            )
            .all()
        )

        total_audits = (
            audits.count()
        )

        total_gps_distance = (
            audits.aggregate(
                total=Sum(
                    "gps_distance_km"
                )
            )["total"]
        )

        audited_km = (
            total_gps_distance
            if total_gps_distance
            is not None
            else 0
        )

        divergences = (
            audits.filter(
                status=(
                    RouteAudit
                    .Status
                    .DIVERGENCE
                )
            )
            .count()
        )

        normal_count = (
            audits.filter(
                status=(
                    RouteAudit
                    .Status
                    .NORMAL
                )
            )
            .count()
        )

        if total_audits:
            regularity_percent = round(
                (
                    normal_count
                    / total_audits
                )
                * 100,
                2,
            )
        else:
            regularity_percent = 0

        recent_audits = (
            audits.order_by(
                "-audited_at",
            )[:5]
        )

        recent_serializer = (
            RouteAuditSerializer(
                recent_audits,
                many=True,
            )
        )

        return Response(
            {
                "audited_km":
                    audited_km,

                "trips":
                    total_audits,

                "divergences":
                    divergences,

                "regularity_percent":
                    regularity_percent,

                "recent_audits":
                    recent_serializer.data,
            },
            status=(
                status.HTTP_200_OK
            ),
        )