# tests/unit/test_rbac_empresas.py
"""RBAC on /api/v1/empresas/*: read = ADMIN/AUDITOR/LIQUIDADOR, write = ADMIN only."""
import pytest
from httpx import AsyncClient

from app.core.security import create_access_token, get_password_hash
from app.models.usuario import Usuario
from app.utils.enums import RolUsuario, EstadoUsuario


async def _headers_for(db_session, rol: RolUsuario, username: str) -> dict:
    usuario = Usuario(
        username=username,
        email=f"{username}@example.com",
        password_hash=get_password_hash("Test1234"),
        nombre_completo=f"Test {rol.value}",
        rol=rol,
        estado=EstadoUsuario.ACTIVO,
    )
    db_session.add(usuario)
    await db_session.commit()
    await db_session.refresh(usuario)
    token = create_access_token(data={"sub": str(usuario.id), "token_version": usuario.token_version})
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
@pytest.mark.parametrize("rol", [RolUsuario.ADMIN, RolUsuario.AUDITOR, RolUsuario.LIQUIDADOR])
async def test_read_empresas_allowed_for_read_roles(client: AsyncClient, db_session, rol):
    headers = await _headers_for(db_session, rol, f"user_{rol.value.lower()}")
    resp = await client.get("/api/v1/empresas/", headers=headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_read_empresas_forbidden_unauthenticated(client: AsyncClient):
    resp = await client.get("/api/v1/empresas/")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_read_empresas_forbidden_for_readonly(client: AsyncClient, db_session):
    """Per explicit project-owner decision, READONLY no longer has ver_empresa --
    it must get a consistent 403 across every Empresas endpoint, matching the
    manual role check already in place on GET /empresas/{id}/empleados.
    """
    headers = await _headers_for(db_session, RolUsuario.READONLY, "readonly_empresas")
    resp = await client.get("/api/v1/empresas/", headers=headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
@pytest.mark.parametrize("rol", [RolUsuario.AUDITOR, RolUsuario.LIQUIDADOR])
async def test_create_empresa_forbidden_for_non_admin(client: AsyncClient, db_session, rol):
    headers = await _headers_for(db_session, rol, f"writer_{rol.value.lower()}")
    resp = await client.post(
        "/api/v1/empresas/",
        headers=headers,
        json={
            "nit": "900999999",
            "razon_social": "Empresa RBAC Test",
            "email_contacto": "rbac@empresa.com",
        },
    )
    assert resp.status_code == 403
