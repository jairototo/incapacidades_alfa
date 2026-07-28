# tests/unit/test_rbac_empleados.py
"""RBAC on /api/v1/empleados/*: read = ADMIN/AUDITOR/LIQUIDADOR, write = ADMIN/AUDITOR only."""
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
async def test_read_empleados_allowed_for_read_roles(client: AsyncClient, db_session, rol):
    headers = await _headers_for(db_session, rol, f"eread_{rol.value.lower()}")
    resp = await client.get("/api/v1/empleados/", headers=headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_read_empleados_forbidden_unauthenticated(client: AsyncClient):
    resp = await client.get("/api/v1/empleados/")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_read_empleados_forbidden_for_readonly(client: AsyncClient, db_session):
    """Per explicit project-owner decision, READONLY no longer has ver_empleado --
    it must get a consistent 403 across every Empleados endpoint, matching the
    manual role check already in place on GET /empresas/{id}/empleados.
    """
    headers = await _headers_for(db_session, RolUsuario.READONLY, "readonly_empleados")
    resp = await client.get("/api/v1/empleados/", headers=headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_create_empleado_forbidden_for_liquidador(client: AsyncClient, db_session, test_empresa):
    headers = await _headers_for(db_session, RolUsuario.LIQUIDADOR, "liquidador_writer")
    resp = await client.post(
        "/api/v1/empleados/",
        headers=headers,
        json={
            "empresa_id": str(test_empresa.id),
            "numero_documento": "1112223334",
            "tipo_documento": "CC",
            "nombres": "Test",
            "apellidos": "Empleado",
            "fecha_ingreso": "2024-01-01",
        },
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_create_empleado_allowed_for_auditor(client: AsyncClient, db_session, test_empresa):
    headers = await _headers_for(db_session, RolUsuario.AUDITOR, "auditor_writer")
    resp = await client.post(
        "/api/v1/empleados/",
        headers=headers,
        json={
            "empresa_id": str(test_empresa.id),
            "numero_documento": "1112223335",
            "tipo_documento": "CC",
            "nombres": "Test",
            "apellidos": "Empleado",
            "fecha_ingreso": "2024-01-01",
        },
    )
    assert resp.status_code == 201
