"""POST /empleados/carga-masiva/confirmar: inserts only valid rows (partial insert)."""
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
async def test_confirmar_carga_masiva_inserts_only_valid_rows(
    client: AsyncClient, db_session, admin_token_headers, test_empresa
):
    content = _build_xlsx([
        ["2000000001", "CC", "Carlos", "Ruiz", "", "", "", "", "", "", "2023-01-01", "", test_empresa.nit],
        ["", "CC", "Sin Documento", "Test", "", "", "", "", "", "", "2023-01-01", "", test_empresa.nit],
    ])

    resp = await client.post(
        "/api/v1/empleados/carga-masiva/confirmar",
        headers=admin_token_headers,
        files={"file": ("empleados.xlsx", content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert resp.status_code == 200
    body = resp.json()

    assert body["insertadas"] == 1
    assert body["con_error"] == 1
    assert body["total_filas"] == 2

    result = await db_session.execute(
        select(Empleado).where(Empleado.numero_documento == "2000000001")
    )
    assert result.scalar_one_or_none() is not None
