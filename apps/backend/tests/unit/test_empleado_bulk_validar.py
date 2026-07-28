"""POST /empleados/carga-masiva/validar: dry-run, writes nothing to the DB."""
import io

import pytest
from httpx import AsyncClient
from openpyxl import Workbook
from sqlalchemy import select

from app.models.empleado import Empleado


def _build_xlsx(rows: list[list]) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.append([
        "numero_documento", "tipo_documento", "nombres", "apellidos", "email",
        "telefono", "fecha_nacimiento", "genero", "cargo", "area",
        "fecha_ingreso", "salario_base", "nit_empresa",
    ])
    for row in rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


@pytest.mark.asyncio
async def test_validar_carga_masiva_detects_errors_and_writes_nothing(
    client: AsyncClient, db_session, admin_token_headers, test_empresa
):
    content = _build_xlsx([
        # Valid row
        ["1000000001", "CC", "Ana", "Gómez", "ana@correo.com", "3001111111",
         "1992-04-10", "F", "Analista", "RRHH", "2023-01-01", "3500000", test_empresa.nit],
        # Missing numero_documento
        ["", "CC", "Luis", "Ramírez", "", "", "", "", "", "", "2023-01-01", "", test_empresa.nit],
        # nit_empresa doesn't exist
        ["1000000002", "CC", "Marta", "Díaz", "", "", "", "", "", "", "2023-01-01", "", "999999999"],
        # Duplicate numero_documento within the file
        ["1000000001", "CC", "Ana", "Duplicada", "", "", "", "", "", "", "2023-01-01", "", test_empresa.nit],
    ])

    resp = await client.post(
        "/api/v1/empleados/carga-masiva/validar",
        headers=admin_token_headers,
        files={"file": ("empleados.xlsx", content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert resp.status_code == 200
    body = resp.json()

    assert body["validas"] == 1
    assert body["con_error"] == 3
    assert body["total_filas"] == 4

    mensajes = [e["mensaje"] for e in body["errores"]]
    assert any("obligatorio" in m.lower() for m in mensajes)
    assert any("999999999" in m for m in mensajes)
    assert any("duplicado" in m.lower() for m in mensajes)

    # Dry-run: nothing inserted.
    result = await db_session.execute(
        select(Empleado).where(Empleado.numero_documento == "1000000001")
    )
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_con_error_and_total_filas_count_rows_not_errors(
    client: AsyncClient, admin_token_headers, test_empresa
):
    """A single row that fails multiple checks must count as ONE row, not one
    per validation error. Regression for con_error/total_filas being computed
    as len(errores) (error count) instead of the distinct number of failing
    rows -- a 2-row file where row 2 fails 3 checks used to report
    total_filas=4 (more rows than the file actually has).
    """
    content = _build_xlsx([
        # Valid row
        ["1000000010", "CC", "Ana", "Gómez", "ana@correo.com", "3001111111",
         "1992-04-10", "F", "Analista", "RRHH", "2023-01-01", "3500000", test_empresa.nit],
        # Row failing 3 independent checks at once: missing numero_documento,
        # missing tipo_documento, missing nombres.
        ["", "", "", "Ramírez", "", "", "", "", "", "", "2023-01-01", "", test_empresa.nit],
    ])

    resp = await client.post(
        "/api/v1/empleados/carga-masiva/validar",
        headers=admin_token_headers,
        files={"file": ("empleados.xlsx", content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert resp.status_code == 200
    body = resp.json()

    assert body["validas"] == 1
    assert body["con_error"] == 1
    assert body["total_filas"] == 2
    # But no error granularity is lost -- all 3 individual errors are still reported.
    assert len(body["errores"]) == 3
