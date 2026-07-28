"""POST /empresas/{id}/regenerar-password: new password, old sessions invalidated."""
import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.usuario import Usuario


@pytest.mark.asyncio
async def test_regenerar_password_returns_new_credentials_and_bumps_token_version(
    client: AsyncClient, db_session, admin_token_headers
):
    create_resp = await client.post(
        "/api/v1/empresas/",
        headers=admin_token_headers,
        json={
            "nit": "900900001",
            "razon_social": "Empresa Regen SAS",
            "email_contacto": "regen@empresa.com",
        },
    )
    empresa_id = create_resp.json()["id"]
    old_password = create_resp.json()["usuario_generado"]["password"]

    result = await db_session.execute(select(Usuario).where(Usuario.empresa_id == empresa_id))
    usuario_before = result.scalar_one()
    token_version_before = usuario_before.token_version

    regen_resp = await client.post(
        f"/api/v1/empresas/{empresa_id}/regenerar-password",
        headers=admin_token_headers,
    )
    assert regen_resp.status_code == 200
    body = regen_resp.json()
    assert body["username"] == "900900001"
    assert body["password"] != old_password

    await db_session.refresh(usuario_before)
    assert usuario_before.token_version == token_version_before + 1
