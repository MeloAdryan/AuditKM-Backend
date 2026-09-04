from django.contrib import admin

from .models import (
    RouteAudit,
    StandardRoute,
    StandardRoutePoint,
    Trip,
    TripLocation,
)


class StandardRoutePointInline(
    admin.TabularInline
):
    model = StandardRoutePoint

    extra = 1

    fields = [
        "sequence",
        "latitude",
        "longitude",
    ]

    ordering = [
        "sequence",
    ]


@admin.register(StandardRoute)
class StandardRouteAdmin(
    admin.ModelAdmin
):
    list_display = [
        "id",
        "name",
        "origin",
        "destination",
        "expected_distance_km",
        "tolerance_percent",
        "corridor_tolerance_m",
        "active",
        "created_at",
    ]

    list_filter = [
        "active",
        "created_at",
    ]

    search_fields = [
        "name",
        "origin",
        "destination",
    ]

    ordering = [
        "name",
    ]

    readonly_fields = [
        "created_at",
        "updated_at",
    ]

    fieldsets = [
        (
            "Identificação",
            {
                "fields": [
                    "name",
                    "origin",
                    "destination",
                    "active",
                ]
            },
        ),
        (
            "Parâmetros da rota",
            {
                "fields": [
                    "expected_distance_km",
                    "expected_duration_minutes",
                    "tolerance_percent",
                    "corridor_tolerance_m",
                ]
            },
        ),
        (
            "Controle",
            {
                "fields": [
                    "created_at",
                    "updated_at",
                ]
            },
        ),
    ]

    inlines = [
        StandardRoutePointInline,
    ]


@admin.register(StandardRoutePoint)
class StandardRoutePointAdmin(
    admin.ModelAdmin
):
    list_display = [
        "id",
        "standard_route",
        "sequence",
        "latitude",
        "longitude",
        "created_at",
    ]

    list_filter = [
        "standard_route",
    ]

    search_fields = [
        "standard_route__name",
    ]

    ordering = [
        "standard_route",
        "sequence",
    ]

    readonly_fields = [
        "created_at",
        "updated_at",
    ]


@admin.register(Trip)
class TripAdmin(
    admin.ModelAdmin
):
    list_display = [
        "id",
        "driver",
        "vehicle",
        "standard_route",
        "origin",
        "destination",
        "status",
        "start_km",
        "end_km",
        "started_at",
        "ended_at",
        "created_at",
    ]

    list_filter = [
        "status",
        "standard_route",
        "vehicle",
        "created_at",
    ]

    search_fields = [
        "driver__username",
        "vehicle__plate",
        "origin",
        "destination",
        "standard_route__name",
    ]

    ordering = [
        "-created_at",
    ]

    readonly_fields = [
        "created_at",
        "updated_at",
    ]

    fieldsets = [
        (
            "Relacionamentos",
            {
                "fields": [
                    "driver",
                    "vehicle",
                    "standard_route",
                ]
            },
        ),
        (
            "Trajeto",
            {
                "fields": [
                    "origin",
                    "destination",
                ]
            },
        ),
        (
            "Quilometragem",
            {
                "fields": [
                    "start_km",
                    "end_km",
                ]
            },
        ),
        (
            "Período",
            {
                "fields": [
                    "started_at",
                    "ended_at",
                ]
            },
        ),
        (
            "Situação",
            {
                "fields": [
                    "status",
                    "notes",
                ]
            },
        ),
        (
            "Controle",
            {
                "fields": [
                    "created_at",
                    "updated_at",
                ]
            },
        ),
    ]


@admin.register(TripLocation)
class TripLocationAdmin(
    admin.ModelAdmin
):
    list_display = [
        "id",
        "trip",
        "latitude",
        "longitude",
        "accuracy",
        "speed",
        "recorded_at",
        "created_at",
    ]

    list_filter = [
        "recorded_at",
        "created_at",
    ]

    search_fields = [
        "trip__id",
        "trip__driver__username",
        "trip__vehicle__plate",
    ]

    ordering = [
        "-recorded_at",
    ]

    readonly_fields = [
        "created_at",
    ]


@admin.register(RouteAudit)
class RouteAuditAdmin(
    admin.ModelAdmin
):
    list_display = [
        "id",
        "trip",
        "standard_route",
        "status",
        "standard_distance_km",
        "gps_distance_km",
        "difference_percent",
        "spatial_deviation_percent",
        "max_deviation_m",
        "outside_points_count",
        "total_points_count",
        "audited_at",
    ]

    list_filter = [
        "status",
        "standard_route",
        "audited_at",
    ]

    search_fields = [
        "trip__driver__username",
        "trip__vehicle__plate",
        "standard_route__name",
    ]

    ordering = [
        "-audited_at",
    ]

    readonly_fields = [
        "trip",
        "standard_route",
        "standard_distance_km",
        "gps_distance_km",
        "odometer_distance_km",
        "difference_km",
        "difference_percent",
        "spatial_deviation_percent",
        "max_deviation_m",
        "outside_points_count",
        "total_points_count",
        "status",
        "audited_at",
    ]

    fieldsets = [
        (
            "Viagem",
            {
                "fields": [
                    "trip",
                    "standard_route",
                ]
            },
        ),
        (
            "Auditoria por distância",
            {
                "fields": [
                    "standard_distance_km",
                    "gps_distance_km",
                    "odometer_distance_km",
                    "difference_km",
                    "difference_percent",
                ]
            },
        ),
        (
            "Auditoria espacial",
            {
                "fields": [
                    "spatial_deviation_percent",
                    "max_deviation_m",
                    "outside_points_count",
                    "total_points_count",
                ]
            },
        ),
        (
            "Resultado",
            {
                "fields": [
                    "status",
                    "justification",
                    "audited_at",
                ]
            },
        ),
    ]