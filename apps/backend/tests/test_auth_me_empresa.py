import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_me_includes_empresa(client: AsyncClient, empresa_user_token: str):
    """GET /auth/me returns empresa_id and an empresa summary for an EMPRESA user."""
    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {empresa_user_token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["rol"] == "EMPRESA"
    assert body["empresa_id"] is not None
    assert body["empresa"]["nit"]
    assert body["empresa"]["razon_social"]
