from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from trips.models import (
    StandardRoute,
    StandardRoutePoint,
    Trip,
)

from trips.services.route_audit import (
    calculate_trip_gps_distance,
)


def _calculate_duration_minutes(
    trip,
):
    """
    Calcula a duração da viagem em minutos.
    """

    if (
        not trip.started_at
        or not trip.ended_at
    ):
        return None

    duration = (
        trip.ended_at
        - trip.started_at
    )

    minutes = round(
        duration.total_seconds()
        / 60
    )

    return max(
        int(minutes),
        1,
    )


@transaction.atomic
def create_standard_route_from_trip(
    trip,
):
    """
    Cria uma rota padrão utilizando os
    pontos GPS de uma viagem finalizada.
    """

    trip = (
        Trip.objects
        .select_for_update()
        .get(
            pk=trip.pk,
        )
    )

    if (
        trip.status
        != Trip.Status.COMPLETED
    ):
        raise ValidationError(
            {
                "trip": (
                    "Somente viagens "
                    "finalizadas podem ser "
                    "transformadas em rota "
                    "padrão."
                )
            }
        )

    if trip.standard_route_id:
        raise ValidationError(
            {
                "standard_route": (
                    "Esta viagem já possui "
                    "uma rota padrão "
                    "associada."
                )
            }
        )

    locations = list(
        trip.locations
        .all()
        .order_by(
            "recorded_at",
            "id",
        )
    )

    if len(locations) < 2:
        raise ValidationError(
            {
                "locations": (
                    "A viagem precisa possuir "
                    "pelo menos dois pontos "
                    "GPS para criar uma rota "
                    "padrão."
                )
            }
        )

    gps_distance = (
        calculate_trip_gps_distance(
            trip
        )
    )

    if (
        gps_distance
        <= Decimal("0.000")
    ):
        raise ValidationError(
            {
                "locations": (
                    "Não foi possível calcular "
                    "uma distância válida com "
                    "os pontos GPS da viagem."
                )
            }
        )

    duration_minutes = (
        _calculate_duration_minutes(
            trip
        )
    )

    route = (
        StandardRoute.objects.create(
            name=(
                f"{trip.origin} → "
                f"{trip.destination} "
                f"(Viagem #{trip.pk})"
            ),
            origin=trip.origin,
            destination=(
                trip.destination
            ),
            expected_distance_km=(
                gps_distance
            ),
            expected_duration_minutes=(
                duration_minutes
            ),
            tolerance_percent=(
                Decimal("10.00")
            ),
            corridor_tolerance_m=100,
            active=True,
        )
    )

    route_points = [
        StandardRoutePoint(
            standard_route=route,
            sequence=index,
            latitude=(
                location.latitude
            ),
            longitude=(
                location.longitude
            ),
        )
        for index, location
        in enumerate(
            locations,
            start=1,
        )
    ]

    StandardRoutePoint.objects.bulk_create(
        route_points
    )

    trip.standard_route = route

    trip.save(
        update_fields=[
            "standard_route",
            "updated_at",
        ]
    )

    return route