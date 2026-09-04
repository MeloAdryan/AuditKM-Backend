from decimal import (
    Decimal,
    ROUND_HALF_UP,
)
from math import (
    cos,
    radians,
    sqrt,
)

from django.core.exceptions import ValidationError

from trips.models import (
    StandardRoute,
    Trip,
)


EARTH_RADIUS_M = 6371008.8


def decimal_value(
    value,
    places="0.01",
):
    return Decimal(
        str(value)
    ).quantize(
        Decimal(places),
        rounding=ROUND_HALF_UP,
    )


def lat_lon_to_local_meters(
    latitude,
    longitude,
    reference_latitude,
    reference_longitude,
):
    """
    Converte latitude/longitude para um
    sistema local aproximado em metros.

    Essa aproximação é adequada para
    trajetos urbanos e regionais.
    """

    latitude_rad = radians(
        float(latitude)
    )

    longitude_rad = radians(
        float(longitude)
    )

    reference_latitude_rad = radians(
        float(reference_latitude)
    )

    reference_longitude_rad = radians(
        float(reference_longitude)
    )

    x = (
        EARTH_RADIUS_M
        * (
            longitude_rad
            - reference_longitude_rad
        )
        * cos(
            reference_latitude_rad
        )
    )

    y = (
        EARTH_RADIUS_M
        * (
            latitude_rad
            - reference_latitude_rad
        )
    )

    return x, y


def point_to_segment_distance_m(
    point_latitude,
    point_longitude,
    start_latitude,
    start_longitude,
    end_latitude,
    end_longitude,
):
    """
    Calcula a menor distância, em metros,
    entre um ponto GPS e um segmento da
    rota padrão.
    """

    reference_latitude = (
        float(point_latitude)
        + float(start_latitude)
        + float(end_latitude)
    ) / 3

    reference_longitude = (
        float(point_longitude)
        + float(start_longitude)
        + float(end_longitude)
    ) / 3

    point_x, point_y = (
        lat_lon_to_local_meters(
            point_latitude,
            point_longitude,
            reference_latitude,
            reference_longitude,
        )
    )

    start_x, start_y = (
        lat_lon_to_local_meters(
            start_latitude,
            start_longitude,
            reference_latitude,
            reference_longitude,
        )
    )

    end_x, end_y = (
        lat_lon_to_local_meters(
            end_latitude,
            end_longitude,
            reference_latitude,
            reference_longitude,
        )
    )

    segment_x = (
        end_x
        - start_x
    )

    segment_y = (
        end_y
        - start_y
    )

    point_vector_x = (
        point_x
        - start_x
    )

    point_vector_y = (
        point_y
        - start_y
    )

    segment_length_squared = (
        segment_x ** 2
        + segment_y ** 2
    )

    if (
        segment_length_squared
        == 0
    ):
        return sqrt(
            (
                point_x
                - start_x
            ) ** 2
            + (
                point_y
                - start_y
            ) ** 2
        )

    projection = (
        (
            point_vector_x
            * segment_x
        )
        + (
            point_vector_y
            * segment_y
        )
    ) / segment_length_squared

    projection = max(
        0.0,
        min(
            1.0,
            projection,
        ),
    )

    closest_x = (
        start_x
        + projection
        * segment_x
    )

    closest_y = (
        start_y
        + projection
        * segment_y
    )

    return sqrt(
        (
            point_x
            - closest_x
        ) ** 2
        + (
            point_y
            - closest_y
        ) ** 2
    )


def distance_to_standard_route_m(
    latitude,
    longitude,
    route_points,
):
    """
    Calcula a menor distância entre um
    TripLocation e qualquer segmento da
    rota padrão.
    """

    if len(route_points) < 2:
        raise ValidationError(
            {
                "standard_route": (
                    "A rota padrão precisa possuir "
                    "pelo menos dois pontos "
                    "geográficos."
                )
            }
        )

    minimum_distance = None

    for index in range(
        len(route_points) - 1
    ):
        start_point = (
            route_points[index]
        )

        end_point = (
            route_points[
                index + 1
            ]
        )

        distance = (
            point_to_segment_distance_m(
                latitude,
                longitude,
                start_point.latitude,
                start_point.longitude,
                end_point.latitude,
                end_point.longitude,
            )
        )

        if (
            minimum_distance
            is None
            or distance
            < minimum_distance
        ):
            minimum_distance = (
                distance
            )

    if minimum_distance is None:
        return 0.0

    return minimum_distance


def calculate_spatial_deviation(
    trip: Trip,
):
    """
    Compara todos os TripLocation da viagem
    com a geometria da StandardRoute.

    Retorna:
        total_points
        outside_points
        outside_percent
        max_deviation_m
    """

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

    standard_route: StandardRoute = (
        trip.standard_route
    )

    route_points = list(
        standard_route
        .points
        .order_by(
            "sequence"
        )
    )

    if len(route_points) < 2:
        raise ValidationError(
            {
                "standard_route": (
                    "A rota padrão precisa possuir "
                    "pelo menos dois pontos para "
                    "análise espacial."
                )
            }
        )

    trip_locations = list(
        trip.locations
        .order_by(
            "recorded_at",
            "id",
        )
    )

    if not trip_locations:
        return {
            "total_points": 0,
            "outside_points": 0,
            "outside_percent":
                Decimal("0.00"),
            "max_deviation_m":
                Decimal("0.00"),
        }

    corridor_tolerance = float(
        standard_route
        .corridor_tolerance_m
    )

    outside_points = 0

    max_deviation = 0.0

    for location in trip_locations:
        distance = (
            distance_to_standard_route_m(
                location.latitude,
                location.longitude,
                route_points,
            )
        )

        max_deviation = max(
            max_deviation,
            distance,
        )

        gps_accuracy = float(
            location.accuracy
            or 0
        )

        effective_tolerance = (
            corridor_tolerance
            + gps_accuracy
        )

        if (
            distance
            > effective_tolerance
        ):
            outside_points += 1

    total_points = len(
        trip_locations
    )

    outside_percent = (
        Decimal(
            outside_points
        )
        / Decimal(
            total_points
        )
        * Decimal("100")
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )

    return {
        "total_points":
            total_points,

        "outside_points":
            outside_points,

        "outside_percent":
            outside_percent,

        "max_deviation_m":
            decimal_value(
                max_deviation,
                "0.01",
            ),
    }