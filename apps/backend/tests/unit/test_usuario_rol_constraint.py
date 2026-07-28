# tests/unit/test_usuario_rol_constraint.py
"""chk_usuario_rol must accept every RolUsuario value, including LIQUIDADOR.

Regression for a bug where RolUsuario.LIQUIDADOR was added to the Python enum
but the DB-level CHECK constraint (originally created in the initial-schema
Alembic migration) was never updated to match, so any INSERT/UPDATE of a
Usuario with rol='LIQUIDADOR' was rejected by a real database. The bug slipped
past every test because tests/conftest.py builds the test schema via
Base.metadata.create_all(), which only creates constraints declared on the ORM
model (__table_args__) -- it never runs Alembic migrations. The fix declares
the constraint on the Usuario model too, so this test's schema (built the same
way the rest of the suite's is) actually exercises it.
"""
import re

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.security import get_password_hash
from app.models.usuario import Usuario
from app.utils.enums import EstadoUsuario, RolUsuario


@pytest.mark.asyncio
async def test_liquidador_role_passes_db_check_constraint(db_session):
    """A Usuario with rol=LIQUIDADOR must actually persist, not just satisfy Pydantic."""
    usuario = Usuario(
        username="liquidador_constraint_test",
        email="liquidador_constraint_test@example.com",
        password_hash=get_password_hash("Test1234"),
        nombre_completo="Usuario Liquidador",
        rol=RolUsuario.LIQUIDADOR,
        estado=EstadoUsuario.ACTIVO,
    )
    db_session.add(usuario)
    await db_session.commit()
    await db_session.refresh(usuario)

    assert usuario.rol == RolUsuario.LIQUIDADOR


@pytest.mark.asyncio
async def test_invalid_rol_still_rejected_by_db_check_constraint(db_session):
    """Sanity check that the constraint is actually active (not accidentally dropped)."""
    usuario = Usuario(
        username="invalid_rol_constraint_test",
        email="invalid_rol_constraint_test@example.com",
        password_hash=get_password_hash("Test1234"),
        nombre_completo="Usuario Rol Invalido",
        rol="NOT_A_REAL_ROLE",
        estado=EstadoUsuario.ACTIVO,
    )
    db_session.add(usuario)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


def test_every_rolusuario_member_is_allowed_by_the_check_constraint():
    """Guard rail: any future RolUsuario addition that forgets to update
    chk_usuario_rol (in both the ORM model and a matching Alembic migration)
    fails loudly here instead of silently passing Pydantic validation and then
    being rejected by the real database.
    """
    constraint = next(
        c for c in Usuario.__table_args__ if getattr(c, "name", None) == "chk_usuario_rol"
    )
    sqltext = str(constraint.sqltext)
    allowed = set(re.findall(r"'([^']+)'", sqltext))

    assert {r.value for r in RolUsuario} <= allowed
