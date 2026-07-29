# tests/unit/test_roles_previsionales.py
"""AUDITOR_PREVISIONALES and AUDITOR_JURIDICO roles must be usable end to end.

Clones the pattern from test_usuario_rol_constraint.py (chk_usuario_rol must
accept every RolUsuario value, including the two new previsionales roles)
and adds coverage for PermissionChecker.PERMISSIONS: both new roles must be
present and ADMIN must keep its explicit allow-list in sync (ADMIN is not a
wildcard in this dict -- see security.py) with the six new previsionales
permissions, or admins would get 403 on previsionales endpoints later.
"""
import re

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.security import Permissions, PermissionChecker, get_password_hash
from app.models.usuario import Usuario
from app.utils.enums import EstadoUsuario, RolUsuario


@pytest.mark.asyncio
async def test_auditor_previsionales_role_passes_db_check_constraint(db_session):
    """A Usuario with rol=AUDITOR_PREVISIONALES must actually persist."""
    usuario = Usuario(
        username="auditor_previsionales_constraint_test",
        email="auditor_previsionales_constraint_test@example.com",
        password_hash=get_password_hash("Test1234"),
        nombre_completo="Usuario Auditor Previsionales",
        rol=RolUsuario.AUDITOR_PREVISIONALES,
        estado=EstadoUsuario.ACTIVO,
    )
    db_session.add(usuario)
    await db_session.commit()
    await db_session.refresh(usuario)

    assert usuario.rol == RolUsuario.AUDITOR_PREVISIONALES


@pytest.mark.asyncio
async def test_auditor_juridico_role_passes_db_check_constraint(db_session):
    """A Usuario with rol=AUDITOR_JURIDICO must actually persist."""
    usuario = Usuario(
        username="auditor_juridico_constraint_test",
        email="auditor_juridico_constraint_test@example.com",
        password_hash=get_password_hash("Test1234"),
        nombre_completo="Usuario Auditor Juridico",
        rol=RolUsuario.AUDITOR_JURIDICO,
        estado=EstadoUsuario.ACTIVO,
    )
    db_session.add(usuario)
    await db_session.commit()
    await db_session.refresh(usuario)

    assert usuario.rol == RolUsuario.AUDITOR_JURIDICO


@pytest.mark.asyncio
async def test_invalid_rol_still_rejected_by_db_check_constraint(db_session):
    """Sanity check that the constraint is still active for made-up roles."""
    usuario = Usuario(
        username="invalid_rol_previsional_constraint_test",
        email="invalid_rol_previsional_constraint_test@example.com",
        password_hash=get_password_hash("Test1234"),
        nombre_completo="Usuario Rol Inventado",
        rol="INVENTADO",
        estado=EstadoUsuario.ACTIVO,
    )
    db_session.add(usuario)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


def test_every_rolusuario_member_is_allowed_by_the_check_constraint():
    """Guard rail: RolUsuario and chk_usuario_rol (ORM __table_args__) must
    stay in sync, including the two new previsionales roles."""
    constraint = next(
        c for c in Usuario.__table_args__ if getattr(c, "name", None) == "chk_usuario_rol"
    )
    sqltext = str(constraint.sqltext)
    allowed = set(re.findall(r"'([^']+)'", sqltext))

    assert {r.value for r in RolUsuario} <= allowed
    assert "AUDITOR_PREVISIONALES" in allowed
    assert "AUDITOR_JURIDICO" in allowed


def test_previsional_permission_constants_exist():
    """The six previsionales permission constants must be defined on Permissions."""
    assert Permissions.PREVISIONAL_READ
    assert Permissions.PREVISIONAL_LOAD
    assert Permissions.PREVISIONAL_AUDIT
    assert Permissions.PREVISIONAL_LIQUIDATE
    assert Permissions.PREVISIONAL_EXPORT
    assert Permissions.PREVISIONAL_LEGAL_REVIEW


def test_auditor_previsionales_role_is_registered_with_previsional_permissions():
    perms = PermissionChecker.PERMISSIONS["AUDITOR_PREVISIONALES"]
    assert Permissions.PREVISIONAL_READ in perms
    assert Permissions.PREVISIONAL_LOAD in perms
    assert Permissions.PREVISIONAL_AUDIT in perms
    assert Permissions.PREVISIONAL_LIQUIDATE in perms
    assert Permissions.PREVISIONAL_EXPORT in perms


def test_auditor_juridico_role_is_registered_with_previsional_permissions():
    perms = PermissionChecker.PERMISSIONS["AUDITOR_JURIDICO"]
    assert Permissions.PREVISIONAL_READ in perms
    assert Permissions.PREVISIONAL_LEGAL_REVIEW in perms


def test_admin_keeps_all_previsional_permissions():
    """ADMIN is an explicit allow-list in PERMISSIONS, not a wildcard --
    it must be updated whenever a new permission is introduced or admins
    get 403 on the new endpoints."""
    admin_perms = PermissionChecker.PERMISSIONS["ADMIN"]
    assert Permissions.PREVISIONAL_READ in admin_perms
    assert Permissions.PREVISIONAL_LOAD in admin_perms
    assert Permissions.PREVISIONAL_AUDIT in admin_perms
    assert Permissions.PREVISIONAL_LIQUIDATE in admin_perms
    assert Permissions.PREVISIONAL_EXPORT in admin_perms
    assert Permissions.PREVISIONAL_LEGAL_REVIEW in admin_perms
