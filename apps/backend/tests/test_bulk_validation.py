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
    good = [doc, "CC", "Ana", "Gómez", "ACCIDENTE_TRABAJO", "2026-06-01", "2026-06-05", 5, "S00.0", "", "Dr X", "RM-1", "", "", "NO", ""]
    bad = [doc, "CC", "Ana", "Gómez", "ACCIDENTE_TRABAJO", "2026-06-10", "2026-06-05", 5, "", "", "Dr X", "RM-1", "", "", "NO", ""]
    empty = ["", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""]
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
