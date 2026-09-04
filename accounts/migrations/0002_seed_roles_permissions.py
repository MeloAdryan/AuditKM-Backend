from django.db import migrations


ROLES = {
    "Administrador": "Acesso completo ao sistema",
    "Diretor": "Acesso estratégico aos dados, relatórios e auditorias",
    "Gestor": "Gerenciamento operacional de motoristas, veículos e viagens",
    "Motorista": "Registro e acompanhamento das próprias viagens",
}


PERMISSIONS = {
    "USER_VIEW": (
        "Visualizar usuários",
        "Permite consultar usuários cadastrados",
    ),
    "USER_MANAGE": (
        "Gerenciar usuários",
        "Permite cadastrar, editar, ativar e inativar usuários",
    ),
    "VEHICLE_VIEW": (
        "Visualizar veículos",
        "Permite consultar veículos cadastrados",
    ),
    "VEHICLE_MANAGE": (
        "Gerenciar veículos",
        "Permite cadastrar, editar, ativar e inativar veículos",
    ),
    "TRIP_CREATE": (
        "Registrar viagem",
        "Permite registrar saída e chegada de viagens",
    ),
    "TRIP_UPDATE": (
        "Editar viagem",
        "Permite alterar informações de viagens",
    ),
    "TRIP_VIEW": (
        "Visualizar viagens",
        "Permite consultar viagens",
    ),
    "TRIP_AUDIT": (
        "Auditar viagem",
        "Permite analisar divergências de quilometragem e rota",
    ),
    "DASHBOARD_VIEW": (
        "Visualizar dashboard",
        "Permite acessar indicadores e gráficos",
    ),
    "REPORT_EXPORT": (
        "Exportar relatórios",
        "Permite gerar e exportar relatórios",
    ),
    "SYSTEM_CONFIG": (
        "Configurar sistema",
        "Permite alterar configurações gerais do AuditKM",
    ),
    "PERMISSION_MANAGE": (
        "Gerenciar permissões",
        "Permite administrar perfis e permissões",
    ),
}


ROLE_PERMISSION_CODES = {
    "Administrador": list(PERMISSIONS.keys()),

    "Diretor": [
        "USER_VIEW",
        "VEHICLE_VIEW",
        "TRIP_VIEW",
        "TRIP_AUDIT",
        "DASHBOARD_VIEW",
        "REPORT_EXPORT",
    ],

    "Gestor": [
        "USER_VIEW",
        "VEHICLE_VIEW",
        "VEHICLE_MANAGE",
        "TRIP_UPDATE",
        "TRIP_VIEW",
        "TRIP_AUDIT",
        "DASHBOARD_VIEW",
        "REPORT_EXPORT",
    ],

    "Motorista": [
        "VEHICLE_VIEW",
        "TRIP_CREATE",
        "TRIP_VIEW",
    ],
}


def create_initial_security_data(apps, schema_editor):
    Role = apps.get_model("accounts", "Role")
    Permission = apps.get_model("accounts", "Permission")
    RolePermission = apps.get_model("accounts", "RolePermission")

    roles = {}

    for role_name, description in ROLES.items():
        role, _ = Role.objects.update_or_create(
            name=role_name,
            defaults={"description": description},
        )
        roles[role_name] = role

    permissions = {}

    for code, (name, description) in PERMISSIONS.items():
        permission, _ = Permission.objects.update_or_create(
            code=code,
            defaults={
                "name": name,
                "description": description,
            },
        )
        permissions[code] = permission

    for role_name, permission_codes in ROLE_PERMISSION_CODES.items():
        role = roles[role_name]

        for code in permission_codes:
            RolePermission.objects.get_or_create(
                role=role,
                permission=permissions[code],
            )


def remove_initial_security_data(apps, schema_editor):
    Role = apps.get_model("accounts", "Role")
    Permission = apps.get_model("accounts", "Permission")

    Role.objects.filter(name__in=ROLES.keys()).delete()
    Permission.objects.filter(code__in=PERMISSIONS.keys()).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            create_initial_security_data,
            remove_initial_security_data,
        ),
    ]