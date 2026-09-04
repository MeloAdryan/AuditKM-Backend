from django.contrib import admin
from .models import Role


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "description",
        "created_at",
    )

    search_fields = (
        "name",
    )

    ordering = (
        "name",
    )