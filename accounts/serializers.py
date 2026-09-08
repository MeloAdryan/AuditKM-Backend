from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Role


User = get_user_model()


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = [
            "id",
            "name",
            "description",
        ]


class UserSerializer(serializers.ModelSerializer):
    role = RoleSerializer(
        read_only=True,
    )

    role_id = serializers.PrimaryKeyRelatedField(
        source="role",
        queryset=Role.objects.all(),
        write_only=True,
        required=True,
    )

    password = serializers.CharField(
        write_only=True,
        required=False,
        min_length=8,
        trim_whitespace=False,
    )

    email = serializers.EmailField(
        required=False,
        allow_blank=True,
    )

    phone = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )

    first_name = serializers.CharField(
        required=False,
        allow_blank=True,
    )

    last_name = serializers.CharField(
        required=False,
        allow_blank=True,
    )

    class Meta:
        model = User

        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "phone",
            "role",
            "role_id",
            "is_active",
            "password",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]


    def validate_username(
        self,
        value,
    ):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "O nome de usuário é obrigatório."
            )

        queryset = User.objects.filter(
            username__iexact=value,
        )

        if self.instance:
            queryset = queryset.exclude(
                pk=self.instance.pk,
            )

        if queryset.exists():
            raise serializers.ValidationError(
                "Já existe um usuário com esse nome."
            )

        return value


    def validate(
        self,
        attrs,
    ):
        request = self.context.get(
            "request",
        )

        if (
            self.instance
            and request
            and request.user == self.instance
            and "role" in attrs
        ):
            new_role = attrs["role"]

            if (
                self.instance.role
                and
                new_role.id
                != self.instance.role.id
            ):
                raise serializers.ValidationError(
                    {
                        "role_id": (
                            "Você não pode alterar "
                            "o próprio perfil de acesso "
                            "por esta tela."
                        )
                    }
                )

        return attrs


    def create(
        self,
        validated_data,
    ):
        password = validated_data.pop(
            "password",
            None,
        )

        if not password:
            raise serializers.ValidationError(
                {
                    "password": (
                        "A senha é obrigatória ao "
                        "cadastrar um funcionário."
                    )
                }
            )

        user = User(
            **validated_data,
        )

        user.set_password(
            password,
        )

        user.save()

        return user


    def update(
        self,
        instance,
        validated_data,
    ):
        password = validated_data.pop(
            "password",
            None,
        )

        for (
            attribute,
            value,
        ) in validated_data.items():
            setattr(
                instance,
                attribute,
                value,
            )

        if password:
            instance.set_password(
                password,
            )

        instance.save()

        return instance