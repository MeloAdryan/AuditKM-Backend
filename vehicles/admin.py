from django.contrib import admin

from .models import Vehicle


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "plate",
        "brand",
        "model",
        "year",
        "current_km",
        "status",
    )

    list_filter = (
        "status",
        "year",
        "brand",
    )

    search_fields = (
        "plate",
        "brand",
        "model",
        "renavam",
        "chassis",
    )

    ordering = ("plate",)

    readonly_fields = (
        "created_at",
        "updated_at",
    )