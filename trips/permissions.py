from rest_framework.permissions import BasePermission


class TripPermission(BasePermission):
    message = (
        "Você não possui permissão "
        "para realizar esta operação."
    )

    permission_map = {
        
      "list": "TRIP_VIEW",
      "retrieve": "TRIP_VIEW",
      "create": "TRIP_CREATE",
      "update": "TRIP_UPDATE",
      "partial_update": "TRIP_UPDATE",
      "audit": "TRIP_AUDIT",

      "locations": "TRIP_VIEW",
    }

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        if user.is_superuser:
            return True

        if not getattr(user, "role", None):
            return False

        # Não permitimos DELETE normal.
        if view.action == "destroy":
            return False

        permission_code = self.permission_map.get(
            view.action
        )

        if not permission_code:
            return False

        return user.role.role_permissions.filter(
            permission__code=permission_code
        ).exists()