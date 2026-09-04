from django.db import models


class Vehicle(models.Model):

    STATUS = [
        ("ACTIVE", "Ativo"),
        ("MAINTENANCE", "Manutenção"),
        ("INACTIVE", "Inativo"),
    ]

    plate = models.CharField(
        "Placa",
        max_length=10,
        unique=True,
    )

    brand = models.CharField(
        "Marca",
        max_length=50,
    )

    model = models.CharField(
        "Modelo",
        max_length=50,
    )

    year = models.PositiveIntegerField(
        "Ano",
    )

    color = models.CharField(
        "Cor",
        max_length=30,
        blank=True,
    )

    renavam = models.CharField(
        "RENAVAM",
        max_length=20,
        unique=True,
    )

    chassis = models.CharField(
        "Chassi",
        max_length=30,
        unique=True,
    )

    current_km = models.PositiveIntegerField(
        "Quilometragem Atual",
        default=0,
    )

    status = models.CharField(
        "Status",
        max_length=20,
        choices=STATUS,
        default="ACTIVE",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "vehicles"
        ordering = ["plate"]
        verbose_name = "Veículo"
        verbose_name_plural = "Veículos"

    def __str__(self):
        return f"{self.plate} - {self.brand} {self.model}"