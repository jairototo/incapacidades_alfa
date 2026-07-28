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


@pytest.mark.asyncio
async def test_create_empresa_rolls_back_if_usuario_insert_fails_after_flush(
    client: AsyncClient, db_session, admin_token_headers
):
    """Proves atomicity of the *actual* two-insert transaction, not just the
    pre-flight email check.

    The `email_contacto` pre-check only guards against a Usuario.email collision,
    checked *before* either `create_flushed` call runs. To exercise the failure
    path the brief describes — Usuario insert fails *after* the Empresa has
    already been flushed — we pre-create a Usuario whose `username` already
    equals the NIT of the empresa we're about to create, but with a different,
    unused email so it slips past the email pre-check. The Usuario insert for
    the new empresa then reuses that same NIT as its username, colliding with
    the `username` unique constraint and raising a real IntegrityError at the
    second `create_flushed` call — after the Empresa row was already flushed.
    """
    from app.models.usuario import Usuario as UsuarioModel
    from app.utils.enums import EstadoUsuario
    from app.core.security import get_password_hash

    db_session.add(UsuarioModel(
        username="900777777",  # will collide with the new empresa's NIT-derived username
        email="username-collision@otraempresa.com",  # different email, so the pre-check passes
        password_hash=get_password_hash("Test1234"),
        nombre_completo="Existing User With Colliding Username",
        rol=RolUsuario.EMPRESA,
        estado=EstadoUsuario.ACTIVO,
    ))
    await db_session.commit()

    resp = await client.post(
        "/api/v1/empresas/",
        headers=admin_token_headers,
        json={
            "nit": "900777777",
            "razon_social": "Empresa Con Colision De Username SAS",
            "email_contacto": "contacto-nuevo@empresasinusuario.com",
        },
    )
    # The IntegrityError raised by the second create_flushed() is caught by the
    # app-wide IntegrityError handler and mapped to 409.
    assert resp.status_code == 409

    # The Session's transaction was rolled back by the failed flush; reset it
    # before issuing further queries on the same test session.
    await db_session.rollback()

    # No orphaned Empresa left behind, even though its row was flushed
    # (and therefore visible within the transaction) before the Usuario insert failed.
    result = await db_session.execute(select(Empresa).where(Empresa.nit == "900777777"))
    assert result.scalar_one_or_none() is None
