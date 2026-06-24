"""
TDD tests for Task 5.1: liquidacion table, model, and metodopagoliquidacion enum.

Tests:
1. Table exists after migration — can query it via raw SQL
2. Liquidacion can be created with mandatory fields only (nullable fields omitted)
3. Liquidacion with all optional fields (including metodo_pago enum)
4. Unique constraint: two liquidaciones for the same incapacidad are rejected
5. CASCADE DELETE: deleting incapacidad also deletes its liquidacion
6. MetodoPagoLiquidacion enum has exactly CHEQUE and OXIRRE values
7. FK to usuario (liquidador_id) is nullable and accepts None
"""
import pytest
from datetime import date
from decimal import Decimal
from uuid import uuid4

import sqlalchemy as sa

from app.utils.enums import MetodoPagoLiquidacion


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _make_incapacidad(db_session) -> sa.engine.row.Row:
    """Insert a minimal ARL Incapacidad row and return its id.

    Uses ARL type (afiliado_id IS NULL) to satisfy the check constraint
    without needing a real empleado/empresa row (those FK columns are nullable).
    """
    inc_id = uuid4()
    await db_session.execute(sa.text("""
        INSERT INTO incapacidad (
            id, numero, tipo, estado, prioridad, prorroga,
            fecha_inicio, fecha_fin, dias_totales, fecha_radicacion,
            created_at, updated_at
        ) VALUES (
            :id, :numero, 'ARL', 'RADICADA', 'NORMAL', false,
            '2026-01-01', '2026-01-10', 10, NOW(),
            NOW(), NOW()
        )
    """), {"id": str(inc_id), "numero": f"INC-TEST-{inc_id.hex[:8]}"})
    await db_session.commit()
    return inc_id


async def _make_liquidacion(db_session, incapacidad_id, **overrides) -> sa.engine.row.Row:
    """Insert a minimal Liquidacion row and return its id."""
    liq_id = uuid4()
    params = {
        "id": str(liq_id),
        "incapacidad_id": str(incapacidad_id),
        "dias_autorizados": overrides.pop("dias_autorizados", 10),
        "fecha_inicio_autorizada": overrides.pop("fecha_inicio_autorizada", date(2026, 1, 1)),
        "fecha_fin_autorizada": overrides.pop("fecha_fin_autorizada", date(2026, 1, 10)),
    }
    params.update(overrides)

    await db_session.execute(sa.text("""
        INSERT INTO liquidacion (
            id, incapacidad_id, dias_autorizados,
            fecha_inicio_autorizada, fecha_fin_autorizada,
            created_at, updated_at
        ) VALUES (
            :id, :incapacidad_id, :dias_autorizados,
            :fecha_inicio_autorizada, :fecha_fin_autorizada,
            NOW(), NOW()
        )
    """), params)
    await db_session.commit()
    return liq_id


# ---------------------------------------------------------------------------
# 1. Table exists and is queryable
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_liquidacion_table_exists(db_session):
    """The liquidacion table exists and SELECT returns without error."""
    result = await db_session.execute(sa.text("SELECT COUNT(*) FROM liquidacion"))
    count = result.scalar()
    assert count is not None


# ---------------------------------------------------------------------------
# 2. Create with mandatory fields only
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_liquidacion_create_minimal(db_session):
    """A Liquidacion can be created with only the mandatory (non-nullable) fields."""
    inc_id = await _make_incapacidad(db_session)
    liq_id = await _make_liquidacion(db_session, inc_id)

    row = await db_session.execute(
        sa.text("SELECT * FROM liquidacion WHERE id = :id"),
        {"id": str(liq_id)},
    )
    liq = row.mappings().one()

    assert str(liq["incapacidad_id"]) == str(inc_id)
    assert liq["dias_autorizados"] == 10
    assert liq["fecha_inicio_autorizada"] == date(2026, 1, 1)
    assert liq["fecha_fin_autorizada"] == date(2026, 1, 10)
    # All optional fields should be NULL
    assert liq["ibl"] is None
    assert liq["valor_total"] is None
    assert liq["metodo_pago"] is None
    assert liq["notas_liquidador"] is None
    assert liq["liquidador_id"] is None


# ---------------------------------------------------------------------------
# 3. Create with all optional fields
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_liquidacion_create_full(db_session):
    """A Liquidacion can be created with all optional fields populated."""
    inc_id = await _make_incapacidad(db_session)
    liq_id = uuid4()

    await db_session.execute(sa.text("""
        INSERT INTO liquidacion (
            id, incapacidad_id, dias_autorizados,
            fecha_inicio_autorizada, fecha_fin_autorizada,
            ibl, periodo_ibl_inicio, periodo_ibl_fin,
            valor_incapacidad_temporal,
            valor_aporte_patronal_pension,
            valor_aporte_trabajador_pension,
            valor_aporte_adicional_trabajador_pension,
            valor_aporte_patronal_salud,
            valor_aporte_trabajador_salud,
            valor_total,
            metodo_pago, notas_liquidador,
            created_at, updated_at
        ) VALUES (
            :id, :incapacidad_id, 10,
            '2026-01-01', '2026-01-10',
            3500000.00, '2025-07-01', '2025-12-31',
            1166666.67,
            420000.00,
            140000.00,
            0.00,
            297500.00,
            140000.00,
            2164166.67,
            'CHEQUE', 'Liquidación de prueba completa',
            NOW(), NOW()
        )
    """), {"id": str(liq_id), "incapacidad_id": str(inc_id)})
    await db_session.commit()

    row = await db_session.execute(
        sa.text("SELECT * FROM liquidacion WHERE id = :id"),
        {"id": str(liq_id)},
    )
    liq = row.mappings().one()

    assert liq["ibl"] == Decimal("3500000.00")
    assert liq["periodo_ibl_inicio"] == date(2025, 7, 1)
    assert liq["periodo_ibl_fin"] == date(2025, 12, 31)
    assert liq["valor_total"] == Decimal("2164166.67")
    assert liq["metodo_pago"] == "CHEQUE"
    assert liq["notas_liquidador"] == "Liquidación de prueba completa"


# ---------------------------------------------------------------------------
# 4. Unique constraint: one liquidacion per incapacidad
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_liquidacion_unique_per_incapacidad(db_session):
    """Creating a second Liquidacion for the same Incapacidad raises IntegrityError."""
    from sqlalchemy.exc import IntegrityError

    inc_id = await _make_incapacidad(db_session)
    await _make_liquidacion(db_session, inc_id)

    with pytest.raises(IntegrityError):
        await _make_liquidacion(db_session, inc_id)


# ---------------------------------------------------------------------------
# 5. CASCADE DELETE: deleting incapacidad deletes liquidacion
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_liquidacion_cascade_delete(db_session):
    """Deleting an Incapacidad cascades to delete its Liquidacion."""
    inc_id = await _make_incapacidad(db_session)
    liq_id = await _make_liquidacion(db_session, inc_id)

    # Verify liquidacion exists
    row = await db_session.execute(
        sa.text("SELECT COUNT(*) FROM liquidacion WHERE id = :id"),
        {"id": str(liq_id)},
    )
    assert row.scalar() == 1

    # Delete the incapacidad — CASCADE should remove the liquidacion
    await db_session.execute(
        sa.text("DELETE FROM incapacidad WHERE id = :id"),
        {"id": str(inc_id)},
    )
    await db_session.commit()

    row = await db_session.execute(
        sa.text("SELECT COUNT(*) FROM liquidacion WHERE id = :id"),
        {"id": str(liq_id)},
    )
    assert row.scalar() == 0, "Liquidacion debe eliminarse en CASCADE al borrar la incapacidad"


# ---------------------------------------------------------------------------
# 6. MetodoPagoLiquidacion enum has exactly CHEQUE and OXIRRE (no DB needed)
# ---------------------------------------------------------------------------

def test_metodo_pago_liquidacion_enum_values():
    """MetodoPagoLiquidacion enum contains exactly CHEQUE and OXIRRE."""
    values = {e.value for e in MetodoPagoLiquidacion}
    assert values == {"CHEQUE", "OXIRRE"}, (
        f"Enum values inesperados: {values}"
    )
    assert MetodoPagoLiquidacion.CHEQUE == "CHEQUE"
    assert MetodoPagoLiquidacion.OXIRRE == "OXIRRE"


# ---------------------------------------------------------------------------
# 7. OXIRRE is also a valid enum value in the DB
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_metodo_pago_oxirre_valid_in_db(db_session):
    """The OXIRRE value is accepted by the PostgreSQL enum type."""
    inc_id = await _make_incapacidad(db_session)
    liq_id = uuid4()

    await db_session.execute(sa.text("""
        INSERT INTO liquidacion (
            id, incapacidad_id, dias_autorizados,
            fecha_inicio_autorizada, fecha_fin_autorizada,
            metodo_pago, created_at, updated_at
        ) VALUES (
            :id, :incapacidad_id, 5,
            '2026-02-01', '2026-02-05',
            'OXIRRE', NOW(), NOW()
        )
    """), {"id": str(liq_id), "incapacidad_id": str(inc_id)})
    await db_session.commit()

    row = await db_session.execute(
        sa.text("SELECT metodo_pago FROM liquidacion WHERE id = :id"),
        {"id": str(liq_id)},
    )
    assert row.scalar() == "OXIRRE"


# ---------------------------------------------------------------------------
# 8. SQLAlchemy ORM model can be created and queried
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_liquidacion_orm_model(db_session):
    """Liquidacion ORM model can be instantiated and saved via the session."""
    from app.models.liquidacion import Liquidacion

    inc_id = await _make_incapacidad(db_session)

    liq = Liquidacion(
        incapacidad_id=inc_id,
        dias_autorizados=7,
        fecha_inicio_autorizada=date(2026, 3, 1),
        fecha_fin_autorizada=date(2026, 3, 7),
        ibl=Decimal("4000000.00"),
        valor_total=Decimal("933333.33"),
        metodo_pago=MetodoPagoLiquidacion.CHEQUE,
        notas_liquidador="ORM test",
    )
    db_session.add(liq)
    await db_session.commit()
    await db_session.refresh(liq)

    assert liq.id is not None
    assert liq.dias_autorizados == 7
    assert liq.ibl == Decimal("4000000.00")
    assert liq.metodo_pago == MetodoPagoLiquidacion.CHEQUE
    assert liq.notas_liquidador == "ORM test"
    assert str(liq).startswith("<Liquidacion(")
