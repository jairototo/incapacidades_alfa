"""
Tests for POST /api/v1/incapacidades/radicar (individual multipart endpoint).
"""
import io
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_radicar_individual_creates_incapacidad(client: AsyncClient, empresa_user_token, test_empleado):
    files = {"incapacidad_medica": ("inc.pdf", io.BytesIO(b"%PDF-1.4 test content here " + b" " * 200), "application/pdf")}
    data = {
        "empleado_id": str(test_empleado.id),
        "tipo_enfermedad": "ACCIDENTE_TRABAJO",
        "fecha_inicio": "2026-06-01", "fecha_fin": "2026-06-05", "dias_totales": "5",
        "diagnostico_cie10": "S00.0", "nombre_medico": "Dr House", "registro_medico": "RM-9",
        "prorroga": "true",
    }
    resp = await client.post("/api/v1/incapacidades/radicar", data=data, files=files,
                             headers={"Authorization": f"Bearer {empresa_user_token}"})
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["total_radicadas"] == 1
    assert body["items"][0]["numero"]


@pytest.mark.asyncio
async def test_radicar_rejects_non_empresa_user(client: AsyncClient, admin_token_headers):
    """ADMIN role should be rejected with 403."""
    files = {"incapacidad_medica": ("inc.pdf", io.BytesIO(b"%PDF-1.4 " + b" " * 200), "application/pdf")}
    data = {
        "empleado_id": "00000000-0000-0000-0000-000000000001",
        "tipo_enfermedad": "ACCIDENTE_TRABAJO",
        "fecha_inicio": "2026-06-01", "fecha_fin": "2026-06-05", "dias_totales": "5",
        "diagnostico_cie10": "S00.0", "nombre_medico": "Dr House", "registro_medico": "RM-9",
    }
    resp = await client.post("/api/v1/incapacidades/radicar", data=data, files=files,
                             headers=admin_token_headers)
    assert resp.status_code == 403
