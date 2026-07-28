"""LIQUIDADOR role: read-only on Empresas and Empleados, no write permissions."""
from app.core.security import PermissionChecker
from app.utils.enums import RolUsuario


def test_liquidador_role_exists():
    assert RolUsuario.LIQUIDADOR == "LIQUIDADOR"


def test_liquidador_has_read_permissions():
    assert PermissionChecker.has_permission("LIQUIDADOR", "ver_empresa")
    assert PermissionChecker.has_permission("LIQUIDADOR", "ver_empleado")


def test_liquidador_has_no_write_permissions():
    assert not PermissionChecker.has_permission("LIQUIDADOR", "crear_empresa")
    assert not PermissionChecker.has_permission("LIQUIDADOR", "editar_empresa")
    assert not PermissionChecker.has_permission("LIQUIDADOR", "eliminar_empresa")
    assert not PermissionChecker.has_permission("LIQUIDADOR", "crear_empleado")
    assert not PermissionChecker.has_permission("LIQUIDADOR", "editar_empleado")
    assert not PermissionChecker.has_permission("LIQUIDADOR", "eliminar_empleado")
