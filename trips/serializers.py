from django.core.exceptions import (
    ValidationError as DjangoValidationError,
)

from rest_framework import serializers

from .models import (
    RouteAudit,
    StandardRoute,
    StandardRoutePoint,
    Trip,
    TripLocation,
)


class StandardRoutePointSerializer(
    serializers.ModelSerializer
):
    class Meta:
        model = StandardRoutePoint

        fields = [
            "id",
            "standard_route",
            "sequence",
            "latitude",
            "longitude",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]


class StandardRouteSerializer(
    serializers.ModelSerializer
):
    points = StandardRoutePointSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = StandardRoute

        fields = [
            "id",
            "name",
            "origin",
            "destination",
            "expected_distance_km",
            "expected_duration_minutes",
            "tolerance_percent",
            "corridor_tolerance_m",
            "active",
            "points",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "points",
            "created_at",
            "updated_at",
        ]


class TripSerializer(
    serializers.ModelSerializer
):
    traveled_km = serializers.IntegerField(
        read_only=True,
    )

    driver_username = serializers.CharField(
        source="driver.username",
        read_only=True,
    )

    vehicle_plate = serializers.CharField(
        source="vehicle.plate",
        read_only=True,
    )

    standard_route = (
        serializers.PrimaryKeyRelatedField(
            queryset=StandardRoute.objects.filter(
                active=True,
            ),
            required=False,
            allow_null=True,
        )
    )

    standard_route_name = serializers.CharField(
        source="standard_route.name",
        read_only=True,
    )

    class Meta:
        model = Trip

        fields = [
            "id",

            "driver",
            "driver_username",

            "vehicle",
            "vehicle_plate",

            "standard_route",
            "standard_route_name",

            "origin",
            "destination",

            "start_km",
            "start_odometer_photo",

            "end_km",
            "end_odometer_photo",

            "started_at",
            "ended_at",

            "status",
            "notes",

            "traveled_km",

            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",

            "driver_username",
            "vehicle_plate",
            "standard_route_name",

            "traveled_km",

            "created_at",
            "updated_at",
        ]

    def create(
        self,
        validated_data,
    ):
        try:
            trip = Trip(
                **validated_data,
            )

            trip.save()

            return trip

        except DjangoValidationError as exc:
            if hasattr(
                exc,
                "message_dict",
            ):
                data = exc.message_dict

            else:
                data = {
                    "detail": exc.messages,
                }

            raise serializers.ValidationError(
                data
            ) from exc

    def update(
        self,
        instance,
        validated_data,
    ):
        for field, value in (
            validated_data.items()
        ):
            setattr(
                instance,
                field,
                value,
            )

        try:
            instance.save()

            return instance

        except DjangoValidationError as exc:
            if hasattr(
                exc,
                "message_dict",
            ):
                data = exc.message_dict

            else:
                data = {
                    "detail": exc.messages,
                }

            raise serializers.ValidationError(
                data
            ) from exc


class TripLocationSerializer(
    serializers.ModelSerializer
):
    class Meta:
        model = TripLocation

        fields = [
            "id",
            "trip",

            "latitude",
            "longitude",

            "accuracy",
            "speed",
            "altitude",
            "heading",

            "recorded_at",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "trip",
            "created_at",
        ]

    def validate(
        self,
        attrs,
    ):
        trip = self.context.get(
            "trip"
        )

        if trip is None:
            raise serializers.ValidationError(
                {
                    "trip": (
                        "A viagem não foi "
                        "informada."
                    )
                }
            )

        location = TripLocation(
            trip=trip,
            **attrs,
        )

        try:
            location.full_clean()

        except DjangoValidationError as exc:
            if hasattr(
                exc,
                "message_dict",
            ):
                data = exc.message_dict

            else:
                data = {
                    "detail": exc.messages,
                }

            raise serializers.ValidationError(
                data
            ) from exc

        return attrs

    def create(
        self,
        validated_data,
    ):
        trip = self.context["trip"]

        try:
            location = TripLocation(
                trip=trip,
                **validated_data,
            )

            location.save()

            return location

        except DjangoValidationError as exc:
            if hasattr(
                exc,
                "message_dict",
            ):
                data = exc.message_dict

            else:
                data = {
                    "detail": exc.messages,
                }

            raise serializers.ValidationError(
                data
            ) from exc


class RouteAuditSerializer(
    serializers.ModelSerializer
):
    trip_id = serializers.IntegerField(
        source="trip.id",
        read_only=True,
    )

    driver_username = serializers.CharField(
        source="trip.driver.username",
        read_only=True,
    )

    vehicle_plate = serializers.CharField(
        source="trip.vehicle.plate",
        read_only=True,
    )

    route_name = serializers.CharField(
        source="standard_route.name",
        read_only=True,
    )

    origin = serializers.CharField(
        source="trip.origin",
        read_only=True,
    )

    destination = serializers.CharField(
        source="trip.destination",
        read_only=True,
    )

    class Meta:
        model = RouteAudit

        fields = [
            "id",

            "trip_id",
            "driver_username",
            "vehicle_plate",

            "route_name",

            "origin",
            "destination",

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
            "justification",

            "audited_at",
        ]

        read_only_fields = [
            "id",

            "trip_id",
            "driver_username",
            "vehicle_plate",

            "route_name",

            "origin",
            "destination",

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