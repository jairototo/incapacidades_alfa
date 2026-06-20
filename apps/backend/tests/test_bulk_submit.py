"""Tests for POST /api/v1/incapacidades/radicar-masiva (bulk submit endpoint)."""
import io
import json
import pytest


@pytest.mark.asyncio
async def test_bulk_submit_creates_all(client, empresa_user_token, test_empleado, seed_cie10):
    eid = str(test_empleado.id)
    filas = [{
        "empleado_id": eid, "tipo_enfermedad": "ACCIDENTE_TRABAJO",
        "fecha_inicio": "2026-06-01", "fecha_fin": "2026-06-05", "dias_totales": 5,
        "diagnostico_cie10": "M545", "nombre_medico": "Dr X", "registro_medico": "RM-1", "prorroga": False,
    }]
    files = [("documentos", (f"{eid}__INCAPACIDAD.pdf", io.BytesIO(b"%PDF-1.4 " + b" " * 200), "application/pdf"))]
    resp = await client.post("/api/v1/incapacidades/radicar-masiva",
        data={"filas": json.dumps(filas)}, files=files,
        headers={"Authorization": f"Bearer {empresa_user_token}"})
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["total_radicadas"] == 1
    assert body["items"][0]["numero"]


@pytest.mark.asyncio
async def test_bulk_submit_rejects_invalid_row(client, empresa_user_token, test_empleado):
    eid = str(test_empleado.id)
    # inverted dates + empty cie10 → invalid; server must reject the batch (422)
    filas = [{
        "empleado_id": eid, "tipo_enfermedad": "ACCIDENTE_TRABAJO",
        "fecha_inicio": "2026-06-10", "fecha_fin": "2026-06-05", "dias_totales": 5,
        "diagnostico_cie10": "", "nombre_medico": "Dr X", "registro_medico": "RM-1", "prorroga": False,
    }]
    resp = await client.post("/api/v1/incapacidades/radicar-masiva",
        data={"filas": json.dumps(filas)}, files=[],
        headers={"Authorization": f"Bearer {empresa_user_token}"})
    assert resp.status_code == 422, resp.text


@pytest.mark.asyncio
async def test_bulk_submit_rejects_nonexistent_cie10(client, empresa_user_token, test_empleado, seed_cie10):
    """U999 cumple el formato pero no existe en el catálogo → el batch se rechaza (422)."""
    eid = str(test_empleado.id)
    filas = [{
        "empleado_id": eid, "tipo_enfermedad": "ACCIDENTE_TRABAJO",
        "fecha_inicio": "2026-06-01", "fecha_fin": "2026-06-05", "dias_totales": 5,
        "diagnostico_cie10": "U999", "nombre_medico": "Dr X", "registro_medico": "RM-1", "prorroga": False,
    }]
    resp = await client.post("/api/v1/incapacidades/radicar-masiva",
        data={"filas": json.dumps(filas)}, files=[],
        headers={"Authorization": f"Bearer {empresa_user_token}"})
    assert resp.status_code == 422, resp.text


@pytest.mark.asyncio
async def test_bulk_submit_reports_bad_document_but_still_creates(client, empresa_user_token, test_empleado, seed_cie10):
    eid = str(test_empleado.id)
    filas = [{
        "empleado_id": eid, "tipo_enfermedad": "ACCIDENTE_TRABAJO",
        "fecha_inicio": "2026-06-01", "fecha_fin": "2026-06-05", "dias_totales": 5,
        "diagnostico_cie10": "M545", "nombre_medico": "Dr X", "registro_medico": "RM-1", "prorroga": False,
    }]
    # An .exe document → DocumentoService extension/MIME validation rejects it → must be reported, not 500
    files = [("documentos", (f"{eid}__INCAPACIDAD.exe", io.BytesIO(b"MZ malicious " + b" " * 200), "application/octet-stream"))]
    resp = await client.post("/api/v1/incapacidades/radicar-masiva",
        data={"filas": json.dumps(filas)}, files=files,
        headers={"Authorization": f"Bearer {empresa_user_token}"})
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["total_radicadas"] == 1          # incapacidad still created
    assert len(body["documentos_ignorados"]) == 1  # the bad doc reported
