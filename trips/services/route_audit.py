from decimal import (
    Decimal,
    ROUND_HALF_UP,
)
from math import (
    atan2,
    cos,
    radians,
    sin,
    sqrt,
)

from django.core.exceptions import ValidationError

from trips.models import (
    RouteAudit,
    Trip,
)

from trips.services.spatial_audit import (
    calculate_spatial_deviation,
)


EARTH_RADIUS_KM = Decimal("6371.0088")


def decimal_value(
    value,
    places="0.001",
):
    return Decimal(
        str(value)
    ).quantize(
        Decimal(places),
        rounding=ROUND_HALF_UP,
    )


def haversine_distance_km(
    latitude_1,
    longitude_1,
    latitude_2,
    longitude_2,
):
    """
    Calcula a distância entre dois pontos
    geográficos utilizando Haversine.
    """

    lat_1 = radians(
        float(latitude_1)
    )

    lon_1 = radians(
        float(longitude_1)
    )

    lat_2 = radians(
        float(latitude_2)
    )

    lon_2 = radians(
        float(longitude_2)
    )

    delta_lat = (
        lat_2
        - lat_1
    )

    delta_lon = (
        lon_2
        - lon_1
    )

    haversine = (
        sin(
            delta_lat / 2
        ) ** 2
        + cos(lat_1)
        * cos(lat_2)
        * sin(
            delta_lon / 2
        ) ** 2
    )

    central_angle = (
        2
        * atan2(
            sqrt(haversine),
            sqrt(
                1 - haversine
            ),
        )
    )

    distance = (
        float(
            EARTH_RADIUS_KM
        )
        * central_angle
    )

    return decimal_value(
        distance,
        "0.001",
    )


def calculate_trip_gps_distance(
    trip: Trip,
):
    """
    Soma a distância entre os TripLocation
    consecutivos da viagem.
    """

    locations = list(
        trip.locations.order_by(
            "recorded_at",
            "id",
        )
    )

    if len(locations) < 2:
        return Decimal("0.000")

    total = Decimal("0.000")

    for index in range(
        len(locations) - 1
    ):
        current = (
            locations[index]
        )

        following = (
            locations[index + 1]
        )

        total += (
            haversine_distance_km(
                current.latitude,
                current.longitude,
                following.latitude,
                following.longitude,
            )
        )

    return total.quantize(
        Decimal("0.001"),
        rounding=ROUND_HALF_UP,
    )


def determine_audit_status(
    difference_percent,
    tolerance_percent,
):
    """
    Classificação pela diferença percentual.

    <= tolerância
        NORMAL

    > tolerância e <= 2x tolerância
        ATTENTION

    > 2x tolerância
        DIVERGENCE
    """

    difference = abs(
        Decimal(
            str(
                difference_percent
            )
        )
    )

    tolerance = Decimal(
        str(
            tolerance_percent
        )
    )

    if difference <= tolerance:
        return (
            RouteAudit.Status.NORMAL
        )

    double_tolerance = (
        tolerance
        * Decimal("2")
    )

    if difference <= double_tolerance:
        return (
            RouteAudit.Status.ATTENTION
        )

    return (
        RouteAudit.Status.DIVERGENCE
    )


def _highest_severity_status(
    first_status,
    second_status,
):
    """
    Retorna o status de maior severidade.
    """

    severity = {
        RouteAudit.Status.NORMAL: 0,
        RouteAudit.Status.ATTENTION: 1,
        RouteAudit.Status.DIVERGENCE: 2,
        RouteAudit.Status.JUSTIFIED: 0,
    }

    if (
        severity.get(
            second_status,
            0,
        )
        >
        severity.get(
            first_status,
            0,
        )
    ):
        return second_status

    return first_status


def generate_route_audit(
    trip: Trip,
):
    """
    Gera ou atualiza a auditoria da viagem.

    A classificação final considera:

    1. diferença de distância;
    2. desvio espacial da polyline.
    """

    if (
        trip.status
        != Trip.Status.COMPLETED
    ):
        raise ValidationError(
            {
                "trip": (
                    "A auditoria só pode ser "
                    "gerada para viagens "
                    "finalizadas."
                )
            }
        )

    if (
        trip.standard_route
        is None
    ):
        raise ValidationError(
            {
                "standard_route": (
                    "A viagem não possui uma "
                    "rota padrão vinculada."
                )
            }
        )

    standard_route = (
        trip.standard_route
    )

    standard_distance = Decimal(
        str(
            standard_route
            .expected_distance_km
        )
    ).quantize(
        Decimal("0.001"),
        rounding=ROUND_HALF_UP,
    )

    gps_distance = (
        calculate_trip_gps_distance(
            trip
        )
    )

    odometer_distance = None

    if (
        trip.start_km is not None
        and trip.end_km is not None
    ):
        odometer_distance = Decimal(
            str(
                trip.end_km
                - trip.start_km
            )
        ).quantize(
            Decimal("0.001"),
            rounding=ROUND_HALF_UP,
        )

    difference_km = (
        gps_distance
        - standard_distance
    ).quantize(
        Decimal("0.001"),
        rounding=ROUND_HALF_UP,
    )

    if (
        standard_distance
        == Decimal("0.000")
    ):
        difference_percent = (
            Decimal("0.00")
        )

    else:
        difference_percent = (
            difference_km
            / standard_distance
            * Decimal("100")
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    distance_status = (
        determine_audit_status(
            difference_percent,
            standard_route
            .tolerance_percent,
        )
    )

    spatial = (
        calculate_spatial_deviation(
            trip
        )
    )

    spatial_status = (
        determine_audit_status(
            spatial[
                "outside_percent"
            ],
            standard_route
            .tolerance_percent,
        )
    )

    final_status = (
        _highest_severity_status(
            distance_status,
            spatial_status,
        )
    )

    audit, _ = (
        RouteAudit.objects
        .update_or_create(
            trip=trip,
            defaults={
                "standard_route":
                    standard_route,

                "standard_distance_km":
                    standard_distance,

                "gps_distance_km":
                    gps_distance,

                "odometer_distance_km":
                    odometer_distance,

                "difference_km":
                    difference_km,

                "difference_percent":
                    difference_percent,

                "spatial_deviation_percent":
                    spatial[
                        "outside_percent"
                    ],

                "max_deviation_m":
                    spatial[
                        "max_deviation_m"
                    ],

                "outside_points_count":
                    spatial[
                        "outside_points"
                    ],

                "total_points_count":
                    spatial[
                        "total_points"
                    ],

                "status":
                    final_status,
            },
        )
    )

    return audit