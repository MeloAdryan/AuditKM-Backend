from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Permission, Role
from vehicles.models import Vehicle


class VehicleAPIRBACTest(APITestCase):

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()

        # =========================================================
        # ROLES
        # Já foram criados pela migration:
        # accounts.0002_seed_roles_permissions
        # =========================================================

        cls.admin_role = Role.objects.get(
            name="Administrador"
        )

        cls.director_role = Role.objects.get(
            name="Diretor"
        )

        cls.manager_role = Role.objects.get(
            name="Gestor"
        )

        cls.driver_role = Role.objects.get(
            name="Motorista"
        )

        # =========================================================
        # PERMISSÕES
        # Também já foram criadas pela migration
        # =========================================================

        cls.vehicle_view = Permission.objects.get(
            code="VEHICLE_VIEW"
        )

        cls.vehicle_manage = Permission.objects.get(
            code="VEHICLE_MANAGE"
        )

        # =========================================================
        # USUÁRIOS DE TESTE
        # =========================================================

        cls.admin = User.objects.create_user(
            username="admin_api",
            password="Senha@123",
            role=cls.admin_role,
        )

        cls.manager = User.objects.create_user(
            username="gestor_api",
            password="Senha@123",
            role=cls.manager_role,
        )

        cls.director = User.objects.create_user(
            username="diretor_api",
            password="Senha@123",
            role=cls.director_role,
        )

        cls.driver = User.objects.create_user(
            username="motorista_api",
            password="Senha@123",
            role=cls.driver_role,
        )

        # Usuário autenticado, mas sem perfil
        cls.no_role_user = User.objects.create_user(
            username="sem_perfil",
            password="Senha@123",
        )

        # Superusuário sem necessidade de role
        cls.superuser = User.objects.create_superuser(
            username="root_api",
            password="Senha@123",
        )

        # =========================================================
        # VEÍCULO BASE PARA OS TESTES
        # =========================================================

        cls.vehicle = Vehicle.objects.create(
            plate="ABC1D23",
            brand="Toyota",
            model="Hilux",
            year=2023,
            color="Branco",
            renavam="12345678901",
            chassis="9BWZZZ377VT004251",
            current_km=10000,
            status="ACTIVE",
        )

    def setUp(self):
        """
        Executado antes de cada teste.
        """

        self.list_url = reverse(
            "vehicle-list"
        )

        self.detail_url = reverse(
            "vehicle-detail",
            kwargs={
                "pk": self.vehicle.pk
            },
        )

        self.new_vehicle = {
            "plate": "XYZ9K88",
            "brand": "Fiat",
            "model": "Strada",
            "year": 2024,
            "color": "Prata",
            "renavam": "98765432100",
            "chassis": "9BWZZZ377VT009999",
            "current_km": 500,
            "status": "ACTIVE",
        }

    def authenticate(self, user):
        """
        Autentica um usuário diretamente na API
        durante os testes.
        """

        self.client.force_authenticate(
            user=user
        )

    # =============================================================
    # USUÁRIO NÃO AUTENTICADO
    # =============================================================

    def test_unauthenticated_user_cannot_list(self):
        response = self.client.get(
            self.list_url
        )

        self.assertIn(
            response.status_code,
            [
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN,
            ],
        )

    # =============================================================
    # USUÁRIO SEM ROLE
    # =============================================================

    def test_user_without_role_cannot_list(self):
        self.authenticate(
            self.no_role_user
        )

        response = self.client.get(
            self.list_url
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    # =============================================================
    # ADMINISTRADOR
    # GET / POST / PUT / PATCH / DELETE
    # =============================================================

    def test_admin_can_list(self):
        self.authenticate(
            self.admin
        )

        response = self.client.get(
            self.list_url
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_admin_can_retrieve(self):
        self.authenticate(
            self.admin
        )

        response = self.client.get(
            self.detail_url
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_admin_can_create(self):
        self.authenticate(
            self.admin
        )

        response = self.client.post(
            self.list_url,
            self.new_vehicle,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertTrue(
            Vehicle.objects.filter(
                plate="XYZ9K88"
            ).exists()
        )

    def test_admin_can_update(self):
        self.authenticate(
            self.admin
        )

        data = {
            "plate": self.vehicle.plate,
            "brand": "Toyota",
            "model": "Hilux SRX",
            "year": 2023,
            "color": "Preto",
            "renavam": self.vehicle.renavam,
            "chassis": self.vehicle.chassis,
            "current_km": 11000,
            "status": "ACTIVE",
        }

        response = self.client.put(
            self.detail_url,
            data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.vehicle.refresh_from_db()

        self.assertEqual(
            self.vehicle.model,
            "Hilux SRX",
        )

        self.assertEqual(
            self.vehicle.current_km,
            11000,
        )

    def test_admin_can_partial_update(self):
        self.authenticate(
            self.admin
        )

        response = self.client.patch(
            self.detail_url,
            {
                "current_km": 12000,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.vehicle.refresh_from_db()

        self.assertEqual(
            self.vehicle.current_km,
            12000,
        )

    def test_admin_can_delete(self):
        self.authenticate(
            self.admin
        )

        response = self.client.delete(
            self.detail_url
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.assertFalse(
            Vehicle.objects.filter(
                pk=self.vehicle.pk
            ).exists()
        )

    # =============================================================
    # GESTOR
    # GET / POST / PUT / PATCH / DELETE
    #
    # Com VEHICLE_MANAGE, atualmente o Gestor pode
    # gerenciar completamente veículos.
    # =============================================================

    def test_manager_can_list(self):
        self.authenticate(
            self.manager
        )

        response = self.client.get(
            self.list_url
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_manager_can_retrieve(self):
        self.authenticate(
            self.manager
        )

        response = self.client.get(
            self.detail_url
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_manager_can_create(self):
        self.authenticate(
            self.manager
        )

        response = self.client.post(
            self.list_url,
            self.new_vehicle,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertTrue(
            Vehicle.objects.filter(
                plate="XYZ9K88"
            ).exists()
        )

    def test_manager_can_update(self):
        self.authenticate(
            self.manager
        )

        response = self.client.patch(
            self.detail_url,
            {
                "status": "MAINTENANCE",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.vehicle.refresh_from_db()

        self.assertEqual(
            self.vehicle.status,
            "MAINTENANCE",
        )

    def test_manager_can_delete(self):
        self.authenticate(
            self.manager
        )

        response = self.client.delete(
            self.detail_url
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.assertFalse(
            Vehicle.objects.filter(
                pk=self.vehicle.pk
            ).exists()
        )

    # =============================================================
    # DIRETOR
    # SOMENTE CONSULTA
    # =============================================================

    def test_director_can_list(self):
        self.authenticate(
            self.director
        )

        response = self.client.get(
            self.list_url
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_director_can_retrieve(self):
        self.authenticate(
            self.director
        )

        response = self.client.get(
            self.detail_url
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_director_cannot_create(self):
        self.authenticate(
            self.director
        )

        response = self.client.post(
            self.list_url,
            self.new_vehicle,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_director_cannot_update(self):
        self.authenticate(
            self.director
        )

        response = self.client.patch(
            self.detail_url,
            {
                "status": "INACTIVE",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_director_cannot_delete(self):
        self.authenticate(
            self.director
        )

        response = self.client.delete(
            self.detail_url
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    # =============================================================
    # MOTORISTA
    # SOMENTE CONSULTA
    # =============================================================

    def test_driver_can_list(self):
        self.authenticate(
            self.driver
        )

        response = self.client.get(
            self.list_url
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_driver_can_retrieve(self):
        self.authenticate(
            self.driver
        )

        response = self.client.get(
            self.detail_url
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_driver_cannot_create(self):
        self.authenticate(
            self.driver
        )

        response = self.client.post(
            self.list_url,
            self.new_vehicle,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_driver_cannot_update(self):
        self.authenticate(
            self.driver
        )

        response = self.client.patch(
            self.detail_url,
            {
                "status": "INACTIVE",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_driver_cannot_delete(self):
        self.authenticate(
            self.driver
        )

        response = self.client.delete(
            self.detail_url
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    # =============================================================
    # SUPERUSUÁRIO
    # =============================================================

    def test_superuser_can_manage_without_role(self):
        self.authenticate(
            self.superuser
        )

        response = self.client.post(
            self.list_url,
            self.new_vehicle,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertTrue(
            Vehicle.objects.filter(
                plate="XYZ9K88"
            ).exists()
        )