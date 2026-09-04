from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from accounts.models import Role
from vehicles.models import Vehicle

from .models import (
    RouteAudit,
    StandardRoute,
    StandardRoutePoint,
    Trip,
    TripLocation,
)

from .services.route_audit import generate_route_audit
from .services.spatial_audit import (
    calculate_spatial_deviation,
    distance_to_standard_route_m,
    point_to_segment_distance_m,
)


User = get_user_model()


class SpatialAuditServiceTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.driver_role, _ = Role.objects.get_or_create(
            name="Motorista",
        )

        cls.driver = User.objects.create_user(
            username="spatial_driver",
            password="123456",
            role=cls.driver_role,
        )

        cls.vehicle = Vehicle.objects.create(
            plate="SPA1A23",
            brand="Toyota",
            model="Hilux",
            year=2024,
            color="Branco",
            renavam="40000000001",
            chassis="SPATIAL_CHASSIS_001",
            current_km=10000,
            status="ACTIVE",
        )

        cls.standard_route = StandardRoute.objects.create(
            name="Rota espacial teste",
            origin="Origem",
            destination="Destino",
            expected_distance_km=Decimal("2.000"),
            expected_duration_minutes=20,
            tolerance_percent=Decimal("10.00"),
            corridor_tolerance_m=100,
            active=True,
        )

        StandardRoutePoint.objects.create(
            standard_route=cls.standard_route,
            sequence=1,
            latitude=Decimal("-9.9740000"),
            longitude=Decimal("-67.8240000"),
        )

        StandardRoutePoint.objects.create(
            standard_route=cls.standard_route,
            sequence=2,
            latitude=Decimal("-9.9740000"),
            longitude=Decimal("-67.8140000"),
        )

        StandardRoutePoint.objects.create(
            standard_route=cls.standard_route,
            sequence=3,
            latitude=Decimal("-9.9740000"),
            longitude=Decimal("-67.8040000"),
        )

    def create_trip(self):
        return Trip.objects.create(
            driver=self.driver,
            vehicle=self.vehicle,
            standard_route=self.standard_route,
            origin="Origem",
            destination="Destino",
            start_km=10000,
            started_at=timezone.now(),
            status=Trip.Status.IN_PROGRESS,
        )

    def create_location(
        self,
        trip,
        latitude,
        longitude,
        accuracy=5.0,
        seconds=0,
    ):
        return TripLocation.objects.create(
            trip=trip,
            latitude=Decimal(str(latitude)),
            longitude=Decimal(str(longitude)),
            accuracy=accuracy,
            speed=5.0,
            altitude=150.0,
            heading=90.0,
            recorded_at=(
                timezone.now()
                + timedelta(seconds=seconds)
            ),
        )

    def test_point_on_route_has_near_zero_distance(self):
        distance = point_to_segment_distance_m(
            -9.9740000,
            -67.8190000,
            -9.9740000,
            -67.8240000,
            -9.9740000,
            -67.8140000,
        )

        self.assertLess(
            distance,
            1.0,
        )

    def test_distance_to_standard_route_uses_nearest_segment(
        self,
    ):
        route_points = list(
            self.standard_route.points.order_by(
                "sequence",
            )
        )

        distance = distance_to_standard_route_m(
            -9.9740000,
            -67.8090000,
            route_points,
        )

        self.assertLess(
            distance,
            1.0,
        )

    def test_point_inside_corridor_is_not_outside(self):
        trip = self.create_trip()

        self.create_location(
            trip=trip,
            latitude=-9.9737000,
            longitude=-67.8190000,
            accuracy=5.0,
        )

        result = calculate_spatial_deviation(
            trip,
        )

        self.assertEqual(
            result["total_points"],
            1,
        )

        self.assertEqual(
            result["outside_points"],
            0,
        )

        self.assertEqual(
            result["outside_percent"],
            Decimal("0.00"),
        )

    def test_point_outside_corridor_is_counted(self):
        trip = self.create_trip()

        self.create_location(
            trip=trip,
            latitude=-9.9710000,
            longitude=-67.8190000,
            accuracy=5.0,
        )

        result = calculate_spatial_deviation(
            trip,
        )

        self.assertEqual(
            result["total_points"],
            1,
        )

        self.assertEqual(
            result["outside_points"],
            1,
        )

        self.assertEqual(
            result["outside_percent"],
            Decimal("100.00"),
        )

        self.assertGreater(
            result["max_deviation_m"],
            Decimal("100.00"),
        )

    def test_gps_accuracy_is_added_to_corridor_tolerance(
        self,
    ):
        trip = self.create_trip()

        self.create_location(
            trip=trip,
            latitude=-9.9728000,
            longitude=-67.8190000,
            accuracy=100.0,
        )

        result = calculate_spatial_deviation(
            trip,
        )

        self.assertEqual(
            result["total_points"],
            1,
        )

        self.assertEqual(
            result["outside_points"],
            0,
        )

    def test_spatial_deviation_percent_is_calculated(self):
        trip = self.create_trip()

        self.create_location(
            trip=trip,
            latitude=-9.9740000,
            longitude=-67.8230000,
            seconds=1,
        )

        self.create_location(
            trip=trip,
            latitude=-9.9740000,
            longitude=-67.8180000,
            seconds=2,
        )

        self.create_location(
            trip=trip,
            latitude=-9.9710000,
            longitude=-67.8130000,
            seconds=3,
        )

        self.create_location(
            trip=trip,
            latitude=-9.9700000,
            longitude=-67.8080000,
            seconds=4,
        )

        result = calculate_spatial_deviation(
            trip,
        )

        self.assertEqual(
            result["total_points"],
            4,
        )

        self.assertEqual(
            result["outside_points"],
            2,
        )

        self.assertEqual(
            result["outside_percent"],
            Decimal("50.00"),
        )

    def test_max_deviation_uses_farthest_point(self):
        trip = self.create_trip()

        self.create_location(
            trip=trip,
            latitude=-9.9738000,
            longitude=-67.8190000,
            seconds=1,
        )

        self.create_location(
            trip=trip,
            latitude=-9.9720000,
            longitude=-67.8190000,
            seconds=2,
        )

        self.create_location(
            trip=trip,
            latitude=-9.9680000,
            longitude=-67.8190000,
            seconds=3,
        )

        result = calculate_spatial_deviation(
            trip,
        )

        self.assertGreater(
            result["max_deviation_m"],
            Decimal("500.00"),
        )

    def test_route_requires_at_least_two_points(self):
        route = StandardRoute.objects.create(
            name="Rota incompleta",
            origin="A",
            destination="B",
            expected_distance_km=Decimal("1.000"),
            expected_duration_minutes=10,
            tolerance_percent=Decimal("10.00"),
            corridor_tolerance_m=100,
            active=True,
        )

        StandardRoutePoint.objects.create(
            standard_route=route,
            sequence=1,
            latitude=Decimal("-9.9740000"),
            longitude=Decimal("-67.8240000"),
        )

        trip = Trip.objects.create(
            driver=self.driver,
            vehicle=self.vehicle,
            standard_route=route,
            origin="A",
            destination="B",
            start_km=10000,
            started_at=timezone.now(),
            status=Trip.Status.IN_PROGRESS,
        )

        with self.assertRaises(
            ValidationError
        ):
            calculate_spatial_deviation(
                trip,
            )


class RouteAuditSpatialIntegrationTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.driver_role, _ = Role.objects.get_or_create(
            name="Motorista",
        )

        cls.driver = User.objects.create_user(
            username="audit_spatial_driver",
            password="123456",
            role=cls.driver_role,
        )

        cls.vehicle = Vehicle.objects.create(
            plate="SPB1A23",
            brand="Volkswagen",
            model="Amarok",
            year=2025,
            color="Prata",
            renavam="40000000002",
            chassis="SPATIAL_CHASSIS_002",
            current_km=20000,
            status="ACTIVE",
        )

        cls.standard_route = StandardRoute.objects.create(
            name="Rota integração espacial",
            origin="Empresa",
            destination="Cliente",
            expected_distance_km=Decimal("2.200"),
            expected_duration_minutes=20,
            tolerance_percent=Decimal("10.00"),
            corridor_tolerance_m=100,
            active=True,
        )

        StandardRoutePoint.objects.create(
            standard_route=cls.standard_route,
            sequence=1,
            latitude=Decimal("-9.9740000"),
            longitude=Decimal("-67.8240000"),
        )

        StandardRoutePoint.objects.create(
            standard_route=cls.standard_route,
            sequence=2,
            latitude=Decimal("-9.9740000"),
            longitude=Decimal("-67.8140000"),
        )

        StandardRoutePoint.objects.create(
            standard_route=cls.standard_route,
            sequence=3,
            latitude=Decimal("-9.9740000"),
            longitude=Decimal("-67.8040000"),
        )

    def test_generate_audit_saves_spatial_metrics(self):
        started_at = timezone.now()

        trip = Trip.objects.create(
            driver=self.driver,
            vehicle=self.vehicle,
            standard_route=self.standard_route,
            origin="Empresa",
            destination="Cliente",
            start_km=20000,
            started_at=started_at,
            status=Trip.Status.IN_PROGRESS,
        )

        TripLocation.objects.create(
            trip=trip,
            latitude=Decimal("-9.9740000"),
            longitude=Decimal("-67.8230000"),
            accuracy=5,
            recorded_at=(
                started_at
                + timedelta(seconds=1)
            ),
        )

        TripLocation.objects.create(
            trip=trip,
            latitude=Decimal("-9.9740000"),
            longitude=Decimal("-67.8140000"),
            accuracy=5,
            recorded_at=(
                started_at
                + timedelta(seconds=2)
            ),
        )

        TripLocation.objects.create(
            trip=trip,
            latitude=Decimal("-9.9700000"),
            longitude=Decimal("-67.8100000"),
            accuracy=5,
            recorded_at=(
                started_at
                + timedelta(seconds=3)
            ),
        )

        TripLocation.objects.create(
            trip=trip,
            latitude=Decimal("-9.9680000"),
            longitude=Decimal("-67.8060000"),
            accuracy=5,
            recorded_at=(
                started_at
                + timedelta(seconds=4)
            ),
        )

        trip.end_km = 20002
        trip.ended_at = (
            started_at
            + timedelta(minutes=20)
        )
        trip.status = Trip.Status.COMPLETED
        trip.save()

        audit = generate_route_audit(
            trip,
        )

        audit.refresh_from_db()

        self.assertEqual(
            audit.total_points_count,
            4,
        )

        self.assertEqual(
            audit.outside_points_count,
            2,
        )

        self.assertEqual(
            audit.spatial_deviation_percent,
            Decimal("50.00"),
        )

        self.assertGreater(
            audit.max_deviation_m,
            Decimal("100.00"),
        )

    def test_spatial_divergence_can_raise_final_status(self):
        started_at = timezone.now()

        trip = Trip.objects.create(
            driver=self.driver,
            vehicle=self.vehicle,
            standard_route=self.standard_route,
            origin="Empresa",
            destination="Cliente",
            start_km=20000,
            started_at=started_at,
            status=Trip.Status.IN_PROGRESS,
        )

        TripLocation.objects.create(
            trip=trip,
            latitude=Decimal("-9.9650000"),
            longitude=Decimal("-67.8200000"),
            accuracy=5,
            recorded_at=(
                started_at
                + timedelta(seconds=1)
            ),
        )

        TripLocation.objects.create(
            trip=trip,
            latitude=Decimal("-9.9640000"),
            longitude=Decimal("-67.8100000"),
            accuracy=5,
            recorded_at=(
                started_at
                + timedelta(seconds=2)
            ),
        )

        trip.end_km = 20002
        trip.ended_at = (
            started_at
            + timedelta(minutes=20)
        )
        trip.status = Trip.Status.COMPLETED
        trip.save()

        audit = generate_route_audit(
            trip,
        )

        audit.refresh_from_db()

        self.assertEqual(
            audit.spatial_deviation_percent,
            Decimal("100.00"),
        )

        self.assertEqual(
            audit.total_points_count,
            2,
        )

        self.assertEqual(
            audit.outside_points_count,
            2,
        )

        self.assertGreater(
            audit.max_deviation_m,
            Decimal("100.00"),
        )

        self.assertEqual(
            audit.status,
            RouteAudit.Status.DIVERGENCE,
        )