from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import Permission, Role, RolePermission


class AccountsModelsTest(TestCase):
    def test_create_role_permission_and_user(self):
        role = Role.objects.create(
            name="Administrador de teste",
            description="Perfil criado durante o teste",
        )

        permission = Permission.objects.create(
            name="Gerenciar usuários de teste",
            code="USER_MANAGE_TEST",
            description="Permissão criada durante o teste",
        )

        role_permission = RolePermission.objects.create(
            role=role,
            permission=permission,
        )

        User = get_user_model()

        user = User.objects.create_user(
            username="usuario_teste",
            password="SenhaForte@123",
            role=role,
        )

        self.assertEqual(user.role, role)
        self.assertTrue(user.check_password("SenhaForte@123"))
        self.assertEqual(role_permission.permission, permission)
        self.assertEqual(str(role), "Administrador de teste")