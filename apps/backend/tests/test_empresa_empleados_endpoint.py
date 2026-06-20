"""Tests for GET /api/v1/empresas/{empresa_id}/empleados (portal employee lookup)."""
import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_empleados_of_my_empresa(client: AsyncClient, empresa_user_token, test_empresa, test_empleado):
    resp = await client.get(
        f"/api/v1/empresas/{test_empresa.id}/empleados",
        headers={"Authorization": f"Bearer {empresa_user_token}"},
    )
    assert resp.status_code == 200, resp.text
    docs = {e["numero_documento"] for e in resp.json()}
    assert test_empleado.numero_documento in docs
    # typed shape (EmpleadoListItem): has created_at, no email/telefono
    first = resp.json()[0]
    assert "created_at" in first and "id" in first and "nombres" in first


@pytest.mark.asyncio
async def test_search_filters_employees(client: AsyncClient, empresa_user_token, test_empresa, test_empleado):
    # non-matching search → empty
    resp = await client.get(
        f"/api/v1/empresas/{test_empresa.id}/empleados",
        params={"search": "zzz-no-match-zzz"},
        headers={"Authorization": f"Bearer {empresa_user_token}"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json() == []
    # search by the employee's name → returns it
    resp2 = await client.get(
        f"/api/v1/empresas/{test_empresa.id}/empleados",
        params={"search": test_empleado.nombres},
        headers={"Authorization": f"Bearer {empresa_user_token}"},
    )
    assert resp2.status_code == 200
    assert any(e["id"] == str(test_empleado.id) for e in resp2.json())


@pytest.mark.asyncio
async def test_empresa_cannot_list_other_company(client: AsyncClient, empresa_user_token):
    other_id = uuid.uuid4()
    resp = await client.get(
        f"/api/v1/empresas/{other_id}/empleados",
        headers={"Authorization": f"Bearer {empresa_user_token}"},
    )
    assert resp.status_code == 403, resp.text
