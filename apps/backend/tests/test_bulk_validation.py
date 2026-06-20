"""Tests for POST /api/v1/incapacidades/radicar-masiva/validar (Excel upload + per-row validation)."""
import io
import pytest
from openpyxl import Workbook
from httpx import AsyncClient
from app.services.bulk_radicacion_service import TEMPLATE_HEADERS


def _xlsx(rows):
    wb = Workbook(); ws = wb.active; ws.append(TEMPLATE_HEADERS)
    for r in rows: ws.append(r)
    buf = io.BytesIO(); wb.save(buf); buf.seek(0); return buf


@pytest.mark.asyncio
async def test_validation_reports_errors_and_skips_empty(client: AsyncClient, empresa_user_token, test_empleado):
    doc = test_empleado.numero_documento
    good = [doc, "CC", "Ana", "Gómez", "ACCIDENTE_TRABAJO", "2026-06-01", "2026-06-05", 5, "S00.0", "", "Dr X", "RM-1", "", "NO", ""]
    bad = [doc, "CC", "Ana", "Gómez", "ACCIDENTE_TRABAJO", "2026-06-10", "2026-06-05", 5, "", "", "Dr X", "RM-1", "", "NO", ""]
    empty = ["", "", "", "", "", "", "", "", "", "", "", "", "", "", ""]
    buf = _xlsx([good, bad, empty])
    resp = await client.post("/api/v1/incapacidades/radicar-masiva/validar",
        files={"archivo": ("data.xlsx", buf, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers={"Authorization": f"Bearer {empresa_user_token}"})
    assert resp.status_code == 200, resp.text
    rows = resp.json()["filas"]
    assert len(rows) == 2  # empty row skipped
    assert rows[0]["valida"] is True and rows[0]["empleado_id"]
    assert rows[1]["valida"] is False
    codigos = {e["codigo"] for e in rows[1]["errores"]}
    assert "INVALID_DATE_RANGE" in codigos and "EMPTY_DIAGNOSTICO_CIE10" in codigos


@pytest.mark.asyncio
async def test_malformed_dias_totales_is_row_error(client: AsyncClient, empresa_user_token, test_empleado):
    doc = test_empleado.numero_documento
    bad = [doc, "CC", "Ana", "Gómez", "ACCIDENTE_TRABAJO", "2026-06-01", "2026-06-05", "cinco", "S00.0", "", "Dr X", "RM-1", "", "NO", ""]
    buf = _xlsx([bad])
    resp = await client.post("/api/v1/incapacidades/radicar-masiva/validar",
        files={"archivo": ("d.xlsx", buf, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers={"Authorization": f"Bearer {empresa_user_token}"})
    assert resp.status_code == 200, resp.text
    rows = resp.json()["filas"]
    assert len(rows) == 1 and rows[0]["valida"] is False
    assert any(e["codigo"] == "INVALID_CELL_VALUE" for e in rows[0]["errores"])


@pytest.mark.asyncio
async def test_bad_date_format_is_row_error(client: AsyncClient, empresa_user_token, test_empleado):
    doc = test_empleado.numero_documento
    bad = [doc, "CC", "Ana", "Gómez", "ACCIDENTE_TRABAJO", "06/01/2026", "2026-06-05", 5, "S00.0", "", "Dr X", "RM-1", "", "NO", ""]
    buf = _xlsx([bad])
    resp = await client.post("/api/v1/incapacidades/radicar-masiva/validar",
        files={"archivo": ("d.xlsx", buf, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers={"Authorization": f"Bearer {empresa_user_token}"})
    assert resp.status_code == 200, resp.text
    assert any(e["codigo"] == "INVALID_CELL_VALUE" for e in resp.json()["filas"][0]["errores"])


@pytest.mark.asyncio
async def test_non_xlsx_upload_returns_400(client: AsyncClient, empresa_user_token):
    import io as _io
    resp = await client.post("/api/v1/incapacidades/radicar-masiva/validar",
        files={"archivo": ("fake.xlsx", _io.BytesIO(b"%PDF-1.4 not an excel"), "application/pdf")},
        headers={"Authorization": f"Bearer {empresa_user_token}"})
    assert resp.status_code == 400, resp.text


@pytest.mark.asyncio
async def test_warning_only_row_is_valid(client: AsyncClient, empresa_user_token, test_empleado):
    doc = test_empleado.numero_documento
    # fecha_inicio 2026-01-01 is >30 days before today (~2026-06-20) => RETROACTIVE_BEYOND_LIMIT (WARNING),
    # dias_totales=10 matches 2026-01-01..2026-01-10 so no mismatch; all required fields present => no ERROR.
    row = [doc, "CC", "Ana", "Gómez", "ACCIDENTE_TRABAJO", "2026-01-01", "2026-01-10", 10, "S00.0", "", "Dr X", "RM-1", "", "NO", ""]
    buf = _xlsx([row])
    resp = await client.post("/api/v1/incapacidades/radicar-masiva/validar",
        files={"archivo": ("d.xlsx", buf, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers={"Authorization": f"Bearer {empresa_user_token}"})
    assert resp.status_code == 200, resp.text
    fila = resp.json()["filas"][0]
    assert fila["valida"] is True  # warning does not block
    codigos = {e["codigo"] for e in fila["errores"]}
    assert "RETROACTIVE_BEYOND_LIMIT" in codigos  # but the warning IS surfaced
    severidades = {e["severidad"] for e in fila["errores"]}
    assert severidades == {"WARNING"}  # only a warning, no error
