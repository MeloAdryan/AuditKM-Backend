from django.contrib.auth import get_user_model

from rest_framework import (
    generics,
    permissions,
    status,
)

from rest_framework.exceptions import (
    PermissionDenied,
)

from rest_framework.response import (
    Response,
)

from rest_framework.views import (
    APIView,
)

from .models import Role

from .serializers import (
    RoleSerializer,
    UserSerializer,
)


User = get_user_model()


def user_is_administrator(
    user,
):
    if (
        not user
        or not user.is_authenticated
    ):
        return False

    if user.is_superuser:
        return True

    return bool(
        user.role
        and
        user.role.name
        == "Administrador"
    )


class IsAdministrator(
    permissions.BasePermission,
):
    message = (
        "Apenas administradores podem "
        "realizar esta operação."
    )

    def has_permission(
        self,
        request,
        view,
    ):
        return user_is_administrator(
            request.user,
        )


class CurrentUserView(
    APIView,
):
    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def get(
        self,
        request,
    ):
        role_data = None

        if request.user.role:
            role_data = {
                "id":
                    request.user.role.id,

                "name":
                    request.user.role.name,
            }

        return Response(
            {
                "id":
                    request.user.id,

                "username":
                    request.user.username,

                "first_name":
                    request.user.first_name,

                "last_name":
                    request.user.last_name,

                "email":
                    request.user.email,

                "phone":
                    request.user.phone,

                "role":
                    role_data,

                "is_staff":
                    request.user.is_staff,

                "is_superuser":
                    request.user.is_superuser,
            }
        )


class DriverListView(
    APIView,
):
    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def get(
        self,
        request,
    ):
        allowed = (
            request.user.is_superuser
            or (
                request.user.role
                and
                request.user.role.name
                in [
                    "Administrador",
                    "Gestor",
                ]
            )
        )

        if not allowed:
            raise PermissionDenied(
                "Você não possui permissão "
                "para listar motoristas."
            )

        drivers = (
            User.objects
            .filter(
                is_active=True,
                role__name="Motorista",
            )
            .select_related(
                "role",
            )
            .order_by(
                "first_name",
                "username",
            )
        )

        data = [
            {
                "id":
                    driver.id,

                "username":
                    driver.username,

                "first_name":
                    driver.first_name,

                "last_name":
                    driver.last_name,

                "email":
                    driver.email,

                "phone":
                    driver.phone,

                "role": (
                    {
                        "id":
                            driver.role.id,

                        "name":
                            driver.role.name,
                    }
                    if driver.role
                    else None
                ),
            }
            for driver in drivers
        ]

        return Response(
            data,
        )


class RoleListView(
    generics.ListAPIView,
):
    permission_classes = [
        permissions.IsAuthenticated,
        IsAdministrator,
    ]

    serializer_class = (
        RoleSerializer
    )

    def get_queryset(
        self,
    ):
        return (
            Role.objects
            .all()
            .order_by(
                "name",
            )
        )


class UserListCreateView(
    generics.ListCreateAPIView,
):
    permission_classes = [
        permissions.IsAuthenticated,
        IsAdministrator,
    ]

    serializer_class = (
        UserSerializer
    )

    def get_queryset(
        self,
    ):
        return (
            User.objects
            .select_related(
                "role",
            )
            .all()
            .order_by(
                "first_name",
                "username",
            )
        )

    def perform_create(
        self,
        serializer,
    ):
        serializer.save()


class UserDetailView(
    generics.RetrieveUpdateDestroyAPIView,
):
    permission_classes = [
        permissions.IsAuthenticated,
        IsAdministrator,
    ]

    serializer_class = (
        UserSerializer
    )

    queryset = (
        User.objects
        .select_related(
            "role",
        )
        .all()
    )

    def destroy(
        self,
        request,
        *args,
        **kwargs,
    ):
        user = self.get_object()

        if (
            user.id
            == request.user.id
        ):
            return Response(
                {
                    "detail": (
                        "Você não pode excluir "
                        "a própria conta "
                        "administrativa."
                    )
                },
                status=(
                    status.HTTP_400_BAD_REQUEST
                ),
            )

        self.perform_destroy(
            user,
        )

        return Response(
            status=(
                status.HTTP_204_NO_CONTENT
            )
        )