from rest_framework.permissions import BasePermission


class VehiclePermission(BasePermission):
    message = "Você não possui permissão para realizar esta operação."

    permission_map = {
        "list": "VEHICLE_VIEW",
        "retrieve": "VEHICLE_VIEW",
        "create": "VEHICLE_MANAGE",
        "update": "VEHICLE_MANAGE",
        "partial_update": "VEHICLE_MANAGE",
        "destroy": "VEHICLE_MANAGE",
    }

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        # Superuser possui acesso total.
        if user.is_superuser:
            return True

        role = getattr(user, "role", None)

        if not role:
            return False

        required_permission = self.permission_map.get(
            view.action
        )

        if not required_permission:
            return False

        return role.role_permissions.filter(
            permission__code=required_permission
        ).exists()