# tests/unit/test_empresa_usuario_creation.py
"""POST /empresas atomically creates a linked Usuario with a generated password."""
import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.usuario import Usuario
from app.models.empresa import Empresa
from app.utils.enums import RolUsuario


@pytest.mark.asyncio
async def test_create_empresa_also_creates_usuario(client: AsyncClient, db_session, admin_token_headers):
    resp = await client.post(
        "/api/v1/empresas/",
        headers=admin_token_headers,
        json={
            "nit": "900555555",
            "razon_social": "Empresa Con Usuario SAS",
            "email_contacto": "contacto@conusuario.com",
        },
    )
    assert resp.status_code == 201
    body = resp.json()

    # Response includes the generated credentials exactly once, here.
    assert body["usuario_generado"]["username"] == "900555555"
    assert len(body["usuario_generado"]["password"]) >= 8

    result = await db_session.execute(
        select(Usuario).where(Usuario.empresa_id == body["id"])
    )
    usuario = result.scalar_one()
    assert usuario.username == "900555555"
    assert usuario.email == "contacto@conusuario.com"
    assert usuario.rol == RolUsuario.EMPRESA
    assert usuario.must_change_password is False


@pytest.mark.asyncio
async def test_create_empresa_duplicate_email_rejected(client: AsyncClient, db_session, admin_token_headers):
    # Create a Usuario with a given email directly, to simulate an already-taken login.
    from app.models.usuario import Usuario as UsuarioModel
    from app.utils.enums import EstadoUsuario
    from app.core.security import get_password_hash

    db_session.add(UsuarioModel(
        username="existing",
        email="ocupado@empresa.com",
        password_hash=get_password_hash("Test1234"),
        nombre_completo="Existing User",
        rol=RolUsuario.EMPRESA,
        estado=EstadoUsuario.ACTIVO,
    ))
    await db_session.commit()

    resp = await client.post(
        "/api/v1/empresas/",
        headers=admin_token_headers,
        json={
            "nit": "900666666",
            "razon_social": "Otra Empresa SAS",
            "email_contacto": "ocupado@empresa.com",
        },
    )
    assert resp.status_code == 409

    # No orphaned Empresa left behind.
    result = await db_session.execute(select(Empresa).where(Empresa.nit == "900666666"))
    assert result.scalar_one_or_none() is None
