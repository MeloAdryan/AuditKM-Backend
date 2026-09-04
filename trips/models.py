from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import (
    MaxValueValidator,
    MinValueValidator,
)
from django.db import models, transaction

from vehicles.models import Vehicle


class StandardRoute(models.Model):
    name = models.CharField(
        max_length=150,
        verbose_name="Nome da rota",
    )

    origin = models.CharField(
        max_length=255,
        verbose_name="Origem",
    )

    destination = models.CharField(
        max_length=255,
        verbose_name="Destino",
    )

    expected_distance_km = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        validators=[
            MinValueValidator(
                Decimal("0.001")
            ),
        ],
        verbose_name="Distância padrão (km)",
    )

    expected_duration_minutes = (
        models.PositiveIntegerField(
            null=True,
            blank=True,
            verbose_name=(
                "Duração esperada (minutos)"
            ),
        )
    )

    tolerance_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("10.00"),
        validators=[
            MinValueValidator(
                Decimal("0.00")
            ),
            MaxValueValidator(
                Decimal("100.00")
            ),
        ],
        verbose_name="Tolerância (%)",
    )

    corridor_tolerance_m = (
        models.PositiveIntegerField(
            default=100,
            validators=[
                MinValueValidator(1),
            ],
            verbose_name=(
                "Tolerância do corredor (m)"
            ),
        )
    )

    active = models.BooleanField(
        default=True,
        verbose_name="Ativa",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criada em",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Atualizada em",
    )

    class Meta:
        db_table = "standard_routes"
        ordering = ["name"]
        verbose_name = "Rota padrão"
        verbose_name_plural = "Rotas padrão"

    def __str__(self):
        return (
            f"{self.name} - "
            f"{self.origin} → "
            f"{self.destination}"
        )


class StandardRoutePoint(models.Model):
    standard_route = models.ForeignKey(
        StandardRoute,
        on_delete=models.CASCADE,
        related_name="points",
        verbose_name="Rota padrão",
    )

    sequence = models.PositiveIntegerField(
        verbose_name="Ordem do ponto",
    )

    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        validators=[
            MinValueValidator(
                Decimal("-90.0000000")
            ),
            MaxValueValidator(
                Decimal("90.0000000")
            ),
        ],
        verbose_name="Latitude",
    )

    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        validators=[
            MinValueValidator(
                Decimal("-180.0000000")
            ),
            MaxValueValidator(
                Decimal("180.0000000")
            ),
        ],
        verbose_name="Longitude",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criado em",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Atualizado em",
    )

    class Meta:
        db_table = "standard_route_points"

        ordering = [
            "standard_route",
            "sequence",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "standard_route",
                    "sequence",
                ],
                name=(
                    "unique_standard_"
                    "route_point_sequence"
                ),
            ),
        ]

        indexes = [
            models.Index(
                fields=[
                    "standard_route",
                    "sequence",
                ],
                name=(
                    "std_route_point_seq_idx"
                ),
            ),
        ]

        verbose_name = (
            "Ponto da rota padrão"
        )

        verbose_name_plural = (
            "Pontos das rotas padrão"
        )

    def __str__(self):
        return (
            f"{self.standard_route.name} - "
            f"Ponto {self.sequence} - "
            f"{self.latitude}, "
            f"{self.longitude}"
        )


class Trip(models.Model):
    class Status(models.TextChoices):
        PLANNED = (
            "PLANNED",
            "Planejada",
        )

        IN_PROGRESS = (
            "IN_PROGRESS",
            "Em andamento",
        )

        COMPLETED = (
            "COMPLETED",
            "Finalizada",
        )

        CANCELLED = (
            "CANCELLED",
            "Cancelada",
        )

    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="trips",
        verbose_name="Motorista",
    )

    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.PROTECT,
        related_name="trips",
        verbose_name="Veículo",
    )

    standard_route = models.ForeignKey(
        StandardRoute,
        on_delete=models.PROTECT,
        related_name="trips",
        null=True,
        blank=True,
        verbose_name="Rota padrão",
    )

    origin = models.CharField(
        max_length=255,
        verbose_name="Origem",
    )

    destination = models.CharField(
        max_length=255,
        verbose_name="Destino",
    )

    start_km = models.PositiveBigIntegerField(
        null=True,
        blank=True,
        verbose_name="Quilometragem inicial",
    )

    end_km = models.PositiveBigIntegerField(
        null=True,
        blank=True,
        verbose_name="Quilometragem final",
    )
    start_odometer_photo = models.ImageField(
    upload_to="trips/odometer/start/",
    null=True,
    blank=True,
    verbose_name="Foto do odômetro inicial",
)

    end_odometer_photo = models.ImageField(
    upload_to="trips/odometer/end/",
    null=True,
    blank=True,
    verbose_name="Foto do odômetro final",
)

    started_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Iniciada em",
    )

    ended_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Finalizada em",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PLANNED,
        verbose_name="Status",
    )

    notes = models.TextField(
        blank=True,
        verbose_name="Observações",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criada em",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Atualizada em",
    )

    class Meta:
        db_table = "trips"
        ordering = ["-created_at"]
        verbose_name = "Viagem"
        verbose_name_plural = "Viagens"

    def clean(self):
        super().clean()

        errors = {}

        # =====================================================
        # TRANSIÇÕES DE STATUS
        # =====================================================

        if self.pk:
            previous_trip = (
                Trip.objects
                .filter(pk=self.pk)
                .only("status")
                .first()
            )

            if previous_trip:
                previous_status = (
                    previous_trip.status
                )

                allowed_transitions = {
                    self.Status.PLANNED: {
                        self.Status.PLANNED,
                        self.Status.IN_PROGRESS,
                        self.Status.CANCELLED,
                    },

                    self.Status.IN_PROGRESS: {
                        self.Status.IN_PROGRESS,
                        self.Status.COMPLETED,
                        self.Status.CANCELLED,
                    },

                    self.Status.COMPLETED: {
                        self.Status.COMPLETED,
                    },

                    self.Status.CANCELLED: {
                        self.Status.CANCELLED,
                    },
                }

                allowed_statuses = (
                    allowed_transitions.get(
                        previous_status,
                        set(),
                    )
                )

                if (
                    self.status
                    not in allowed_statuses
                ):
                    errors["status"] = (
                        "Transição de status "
                        "inválida: "
                        f"{previous_status} → "
                        f"{self.status}."
                    )

        # =====================================================
        # QUILOMETRAGEM
        # =====================================================

        if (
            self.start_km is not None
            and self.end_km is not None
            and self.end_km < self.start_km
        ):
            errors["end_km"] = (
                "A quilometragem final não "
                "pode ser menor que a "
                "quilometragem inicial."
            )

        # NOVO:
        # A quilometragem final também não pode
        # ser menor que a quilometragem atual
        # registrada no veículo.
        if (
            self.vehicle_id
            and self.end_km is not None
            and self.status
            == self.Status.COMPLETED
        ):
            vehicle_current_km = (
                self.vehicle.current_km
            )

            if (
                vehicle_current_km
                is not None
                and self.end_km
                < vehicle_current_km
            ):
                errors["end_km"] = (
                    "A quilometragem final não "
                    "pode ser menor que a "
                    "quilometragem atual do "
                    "veículo "
                    f"({vehicle_current_km} km)."
                )

        if (
            self.vehicle_id
            and self.start_km is not None
            and self.status
            == self.Status.IN_PROGRESS
        ):
            vehicle_current_km = (
                self.vehicle.current_km
            )

            if (
                vehicle_current_km
                is not None
                and self.start_km
                < vehicle_current_km
            ):
                errors["start_km"] = (
                    "A quilometragem inicial "
                    "não pode ser menor que a "
                    "quilometragem atual do "
                    "veículo "
                    f"({vehicle_current_km} km)."
                )

        # =====================================================
        # VIAGEM FINALIZADA
        # =====================================================

        if (
            self.status
            == self.Status.COMPLETED
        ):
            if self.end_km is None:
                errors["end_km"] = (
                    "Informe a quilometragem "
                    "final para finalizar a "
                    "viagem."
                )

            if self.ended_at is None:
                errors["ended_at"] = (
                    "Informe a data/hora de "
                    "finalização da viagem."
                )

        # =====================================================
        # VIAGEM EM ANDAMENTO
        # =====================================================

        if (
            self.status
            == self.Status.IN_PROGRESS
        ):
            if self.start_km is None:
                errors["start_km"] = (
                    "Informe a quilometragem "
                    "inicial para iniciar a "
                    "viagem."
                )

            if self.started_at is None:
                errors["started_at"] = (
                    "Informe a data/hora de "
                    "início da viagem."
                )

        # =====================================================
        # DATAS
        # =====================================================

        if (
            self.started_at is not None
            and self.ended_at is not None
            and self.ended_at
            < self.started_at
        ):
            errors["ended_at"] = (
                "A data/hora final não pode "
                "ser anterior ao início."
            )

        # =====================================================
        # MOTORISTA
        # =====================================================

        if (
            self.driver_id
            and self.status
            == self.Status.IN_PROGRESS
        ):
            driver_trip = (
                Trip.objects.filter(
                    driver_id=self.driver_id,
                    status=(
                        self.Status.IN_PROGRESS
                    ),
                )
            )

            if self.pk:
                driver_trip = (
                    driver_trip.exclude(
                        pk=self.pk
                    )
                )

            if driver_trip.exists():
                errors["driver"] = (
                    "Este motorista já possui "
                    "uma viagem em andamento."
                )

        # =====================================================
        # VEÍCULO
        # =====================================================

        if (
            self.vehicle_id
            and self.status
            == self.Status.IN_PROGRESS
        ):
            vehicle_trip = (
                Trip.objects.filter(
                    vehicle_id=self.vehicle_id,
                    status=(
                        self.Status.IN_PROGRESS
                    ),
                )
            )

            if self.pk:
                vehicle_trip = (
                    vehicle_trip.exclude(
                        pk=self.pk
                    )
                )

            if vehicle_trip.exists():
                errors["vehicle"] = (
                    "Este veículo já está em "
                    "outra viagem em andamento."
                )

        if errors:
            raise ValidationError(errors)

    def save(
        self,
        *args,
        **kwargs,
    ):
        self.full_clean()

        with transaction.atomic():
            previous_status = None

            if self.pk:
                previous_status = (
                    Trip.objects
                    .filter(pk=self.pk)
                    .values_list(
                        "status",
                        flat=True,
                    )
                    .first()
                )

            result = super().save(
                *args,
                **kwargs,
            )

            became_completed = (
                self.status
                == self.Status.COMPLETED
                and previous_status
                != self.Status.COMPLETED
            )

            if (
                became_completed
                and self.end_km
                is not None
                and self.vehicle_id
            ):
                vehicle = (
                    Vehicle.objects
                    .select_for_update()
                    .get(
                        pk=self.vehicle_id
                    )
                )

                vehicle.current_km = (
                    self.end_km
                )

                vehicle.save(
                    update_fields=[
                        "current_km",
                        "updated_at",
                    ],
                )

            return result

    @property
    def traveled_km(self):
        if (
            self.start_km is None
            or self.end_km is None
        ):
            return None

        return (
            self.end_km
            - self.start_km
        )

    def __str__(self):
        return (
            f"Viagem #{self.pk} - "
            f"{self.driver.username} - "
            f"{self.vehicle.plate}"
        )


class TripLocation(models.Model):
    trip = models.ForeignKey(
        Trip,
        on_delete=models.CASCADE,
        related_name="locations",
        verbose_name="Viagem",
    )

    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        validators=[
            MinValueValidator(
                Decimal("-90.0000000")
            ),
            MaxValueValidator(
                Decimal("90.0000000")
            ),
        ],
        verbose_name="Latitude",
    )

    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        validators=[
            MinValueValidator(
                Decimal("-180.0000000")
            ),
            MaxValueValidator(
                Decimal("180.0000000")
            ),
        ],
        verbose_name="Longitude",
    )

    accuracy = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Precisão (m)",
    )

    speed = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Velocidade (m/s)",
    )

    altitude = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Altitude (m)",
    )

    heading = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Direção",
    )

    recorded_at = models.DateTimeField(
        verbose_name="Registrado em",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=(
            "Recebido pelo servidor em"
        ),
    )

    class Meta:
        db_table = "trip_locations"

        ordering = [
            "recorded_at",
        ]

        indexes = [
            models.Index(
                fields=[
                    "trip",
                    "recorded_at",
                ],
                name=(
                    "trip_location_time_idx"
                ),
            ),
        ]

        verbose_name = (
            "Localização da viagem"
        )

        verbose_name_plural = (
            "Localizações das viagens"
        )

    def clean(self):
        super().clean()

        if (
            self.trip_id
            and self.trip.status
            != Trip.Status.IN_PROGRESS
        ):
            raise ValidationError(
                {
                    "trip": (
                        "Localizações só podem "
                        "ser registradas em "
                        "viagens em andamento."
                    ),
                },
            )

    def save(
        self,
        *args,
        **kwargs,
    ):
        self.full_clean()

        return super().save(
            *args,
            **kwargs,
        )

    def __str__(self):
        return (
            f"Viagem #{self.trip_id} - "
            f"{self.latitude}, "
            f"{self.longitude}"
        )


class RouteAudit(models.Model):
    class Status(models.TextChoices):
        NORMAL = (
            "NORMAL",
            "Normal",
        )

        ATTENTION = (
            "ATTENTION",
            "Atenção",
        )

        DIVERGENCE = (
            "DIVERGENCE",
            "Divergência",
        )

        JUSTIFIED = (
            "JUSTIFIED",
            "Justificado",
        )

    trip = models.OneToOneField(
        Trip,
        on_delete=models.CASCADE,
        related_name="route_audit",
        verbose_name="Viagem",
    )

    standard_route = models.ForeignKey(
        StandardRoute,
        on_delete=models.PROTECT,
        related_name="audits",
        verbose_name="Rota padrão",
    )

    standard_distance_km = (
        models.DecimalField(
            max_digits=10,
            decimal_places=3,
            verbose_name=(
                "Distância padrão (km)"
            ),
        )
    )

    gps_distance_km = (
        models.DecimalField(
            max_digits=10,
            decimal_places=3,
            verbose_name=(
                "Distância GPS (km)"
            ),
        )
    )

    odometer_distance_km = (
        models.DecimalField(
            max_digits=10,
            decimal_places=3,
            null=True,
            blank=True,
            verbose_name=(
                "Distância do odômetro (km)"
            ),
        )
    )

    difference_km = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        verbose_name="Diferença (km)",
    )

    difference_percent = (
        models.DecimalField(
            max_digits=8,
            decimal_places=2,
            verbose_name="Diferença (%)",
        )
    )

    # =========================================================
    # AUDITORIA ESPACIAL
    # =========================================================

    spatial_deviation_percent = (
        models.DecimalField(
            max_digits=5,
            decimal_places=2,
            default=Decimal("0.00"),
            validators=[
                MinValueValidator(
                    Decimal("0.00")
                ),
                MaxValueValidator(
                    Decimal("100.00")
                ),
            ],
            verbose_name=(
                "Pontos fora da rota (%)"
            ),
        )
    )

    max_deviation_m = (
        models.DecimalField(
            max_digits=10,
            decimal_places=2,
            default=Decimal("0.00"),
            validators=[
                MinValueValidator(
                    Decimal("0.00")
                ),
            ],
            verbose_name=(
                "Maior afastamento "
                "da rota (m)"
            ),
        )
    )

    outside_points_count = (
        models.PositiveIntegerField(
            default=0,
            verbose_name=(
                "Pontos fora da rota"
            ),
        )
    )

    total_points_count = (
        models.PositiveIntegerField(
            default=0,
            verbose_name=(
                "Total de pontos analisados"
            ),
        )
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        verbose_name="Resultado",
    )

    justification = models.TextField(
        blank=True,
        verbose_name="Justificativa",
    )

    audited_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Auditada em",
    )

    class Meta:
        db_table = "route_audits"

        ordering = [
            "-audited_at",
        ]

        verbose_name = (
            "Auditoria de rota"
        )

        verbose_name_plural = (
            "Auditorias de rota"
        )

    def __str__(self):
        return (
            "Auditoria viagem "
            f"#{self.trip_id} - "
            f"{self.status}"
        )