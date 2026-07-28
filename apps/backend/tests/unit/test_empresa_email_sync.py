# tests/unit/test_empresa_email_sync.py
"""PATCH /empresas/{id}: editing email_contacto updates the linked Usuario.email too."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_update_email_contacto_syncs_usuario_email(client: AsyncClient, admin_token_headers):
    create_resp = await client.post(
        "/api/v1/empresas/",
        headers=admin_token_headers,
        json={
            "nit": "900777777",
            "razon_social": "Empresa Sync SAS",
            "email_contacto": "viejo@sync.com",
        },
    )
    empresa_id = create_resp.json()["id"]

    update_resp = await client.put(
        f"/api/v1/empresas/{empresa_id}",
        headers=admin_token_headers,
        json={"email_contacto": "nuevo@sync.com"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["email_contacto"] == "nuevo@sync.com"

    me_check = await client.post(
        "/api/v1/empresas/",
        headers=admin_token_headers,
        json={
            "nit": "900788888",
            "razon_social": "Otra Empresa SAS",
            "email_contacto": "nuevo@sync.com",
        },
    )
    # "nuevo@sync.com" is now the first empresa's login — creating a second
    # empresa with the same email must be rejected.
    assert me_check.status_code == 409


@pytest.mark.asyncio
async def test_update_email_contacto_conflict_with_other_empresa(client: AsyncClient, admin_token_headers):
    await client.post(
        "/api/v1/empresas/",
        headers=admin_token_headers,
        json={"nit": "900800001", "razon_social": "Empresa A", "email_contacto": "a@dup.com"},
    )
    resp_b = await client.post(
        "/api/v1/empresas/",
        headers=admin_token_headers,
        json={"nit": "900800002", "razon_social": "Empresa B", "email_contacto": "b@dup.com"},
    )
    empresa_b_id = resp_b.json()["id"]

    update_resp = await client.put(
        f"/api/v1/empresas/{empresa_b_id}",
        headers=admin_token_headers,
        json={"email_contacto": "a@dup.com"},
    )
    assert update_resp.status_code == 409
