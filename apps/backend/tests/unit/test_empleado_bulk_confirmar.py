"""POST /empleados/carga-masiva/confirmar: inserts only valid rows (partial insert)."""
import io
from uuid import uuid4

import pytest
from httpx import AsyncClient
from openpyxl import Workbook
from sqlalchemy import select

from app.db.repositories.empleado_repository import empleado_repository
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


@pytest.mark.asyncio
async def test_confirmar_carga_masiva_insert_failure_does_not_cascade(
    client: AsyncClient, db_session, admin_token_headers, test_empresa, monkeypatch
):
    """A single row's *insert-time* failure (e.g. a genuine IntegrityError) must not
    poison the DB session for the rest of the batch, and must not be double-counted
    in total_filas.

    All three rows here pass validation (parsear_y_validar_empleados finds nothing
    wrong with any of them). The middle row is made to fail at insert time by
    monkeypatching empleado_repository.create to force a real IntegrityError
    (FK violation on empresa_id) for that one document only, before delegating to
    the real create() for every other row. Without `await db.rollback()` in the
    except branch, SQLAlchemy leaves the AsyncSession in "pending rollback" state
    after that failed commit, and the next row's *genuinely valid* insert also
    raises (a fabricated failure) -- that's the cascading-failure bug this proves
    is fixed.
    """
    content = _build_xlsx([
        ["3000000001", "CC", "Ana", "Primera", "", "", "", "", "", "", "2023-01-01", "", test_empresa.nit],
        ["3000000002", "CC", "Beto", "Segundo", "", "", "", "", "", "", "2023-01-01", "", test_empresa.nit],
        ["3000000003", "CC", "Caro", "Tercera", "", "", "", "", "", "", "2023-01-01", "", test_empresa.nit],
    ])

    original_create = empleado_repository.create

    async def flaky_create(db, data):
        if data["numero_documento"] != "3000000002":
            return await original_create(db, data)
        # Force a genuine DB-level IntegrityError (FK violation) for this one row,
        # instead of the valid empresa_id parsear_y_validar_empleados resolved.
        bad_data = dict(data)
        bad_data["empresa_id"] = uuid4()
        return await original_create(db, bad_data)

    monkeypatch.setattr(empleado_repository, "create", flaky_create)

    resp = await client.post(
        "/api/v1/empleados/carga-masiva/confirmar",
        headers=admin_token_headers,
        files={"file": ("empleados.xlsx", content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert resp.status_code == 200
    body = resp.json()

    # True row count in the file -- not inflated by the insert-time failure.
    assert body["total_filas"] == 3
    assert body["insertadas"] == 2
    assert body["con_error"] == 1

    # The row *before* the failure was inserted (unaffected either way).
    result = await db_session.execute(
        select(Empleado).where(Empleado.numero_documento == "3000000001")
    )
    assert result.scalar_one_or_none() is not None

    # The failing row itself was never inserted.
    result = await db_session.execute(
        select(Empleado).where(Empleado.numero_documento == "3000000002")
    )
    assert result.scalar_one_or_none() is None

    # The row *after* the failure still got inserted -- proves the rollback fix:
    # without it, the poisoned session would turn this genuinely valid row into
    # another fabricated failure.
    result = await db_session.execute(
        select(Empleado).where(Empleado.numero_documento == "3000000003")
    )
    assert result.scalar_one_or_none() is not None
