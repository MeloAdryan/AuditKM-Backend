from django.contrib.auth import get_user_model

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


User = get_user_model()


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        role = None

        if getattr(user, "role", None):
            role = {
                "id": user.role.id,
                "name": user.role.name,
            }

        return Response(
            {
                "id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "role": role,
                "is_staff": user.is_staff,
                "is_superuser": user.is_superuser,
            }
        )


class DriverListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        role_name = (
            user.role.name
            if getattr(user, "role", None)
            else None
        )

        can_list_drivers = (
            user.is_superuser
            or role_name in {
                "Administrador",
                "Gestor",
            }
        )

        if not can_list_drivers:
            return Response(
                {
                    "detail": (
                        "Seu perfil não possui permissão "
                        "para listar motoristas."
                    )
                },
                status=403,
            )

        drivers = User.objects.filter(
            role__name="Motorista",
            is_active=True,
        ).order_by(
            "first_name",
            "last_name",
            "username",
        )

        data = [
            {
                "id": driver.id,
                "username": driver.username,
                "first_name": driver.first_name,
                "last_name": driver.last_name,
            }
            for driver in drivers
        ]

        return Response(data)