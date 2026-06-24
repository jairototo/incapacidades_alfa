"""
TDD tests for Task 5.2: Liquidacion service + endpoints.

Tests:
1.  devolucion_requiere_observacion — BadRequestException when observacion=""
2.  devolucion_desde_estado_invalido — InvalidStateException when not in LIQUIDACION/LIQUIDACION_PARCIAL
3.  devolucion_exitosa_desde_liquidacion — transitions to EN_AUDITORIA
4.  devolucion_exitosa_desde_liquidacion_parcial — transitions to EN_AUDITORIA
5.  guardar_liquidacion_crea_registro — crea registro en DB
6.  guardar_liquidacion_actualiza_registro — segunda llamada actualiza (no duplica)
7.  guardar_liquidacion_estado_invalido — InvalidStateException when not in LIQUIDACION
8.  get_liquidacion_not_found — NotFoundException when no liquidacion exists
9.  calcular_ibl_stub_retorna_null — always returns ibl=None
10. calcular_breakdown_placeholder_all_none — all values None while C1 pending
11. calcular_breakdown_ibl_none — None ibl returns all None breakdown
12. completar_liquidacion_a_pagada — LIQUIDACION → PAGADA
13. completar_liquidacion_a_pagada_parcial — LIQUIDACION_PARCIAL → PAGADA_PARCIAL
14. completar_liquidacion_sin_registro — NotFoundException if no liquidacion saved
"""
import pytest
import sqlalchemy as sa
from datetime import date
from decimal import Decimal
from uuid import uuid4

from app.core.exceptions import BadRequestException, InvalidStateException, NotFoundException
from app.utils.enums import EstadoIncapacidad


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _make_incapacidad(db_session, estado: str = "LIQUIDACION") -> sa.engine.Row:
    """Insert a minimal incapacidad in the given estado and return its id."""
    inc_id = uuid4()
    await db_session.execute(sa.text("""
        INSERT INTO incapacidad (
            id, numero, tipo, estado, prioridad, prorroga,
            fecha_inicio, fecha_fin, dias_totales, fecha_radicacion,
            created_at, updated_at
        ) VALUES (
            :id, :numero, 'ARL', :estado, 'NORMAL', false,
            '2026-01-01', '2026-01-10', 10, NOW(),
            NOW(), NOW()
        )
    """), {"id": str(inc_id), "numero": f"INC-TEST-{inc_id.hex[:8]}", "estado": estado})
    await db_session.commit()
    return inc_id


async def _make_liquidador(db_session) -> "UUID":
    """Create a minimal usuario (AUDITOR role) via ORM and return its id."""
    from app.models.usuario import Usuario
    from app.utils.enums import RolUsuario, EstadoUsuario
    from app.core.security import get_password_hash

    uid = uuid4()
    usuario = Usuario(
        username=f"liq_{uid.hex[:6]}",
        email=f"liq_{uid.hex[:6]}@test.com",
        password_hash=get_password_hash("Test123!"),
        nombre_completo="Liquidador Test",
        rol=RolUsuario.AUDITOR,
        estado=EstadoUsuario.ACTIVO,
    )
    db_session.add(usuario)
    await db_session.commit()
    await db_session.refresh(usuario)
    return usuario.id


async def _make_liquidacion_row(db_session, incapacidad_id) -> None:
    """Insert a minimal liquidacion row for the given incapacidad."""
    liq_id = uuid4()
    await db_session.execute(sa.text("""
        INSERT INTO liquidacion (
            id, incapacidad_id, dias_autorizados,
            fecha_inicio_autorizada, fecha_fin_autorizada,
            created_at, updated_at
        ) VALUES (
            :id, :inc_id, 10,
            '2026-01-01', '2026-01-10',
            NOW(), NOW()
        )
    """), {"id": str(liq_id), "inc_id": str(incapacidad_id)})
    await db_session.commit()


# ---------------------------------------------------------------------------
# 1. Devolution requires non-empty observacion
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_devolucion_requiere_observacion(db_session):
    """BadRequestException when observacion is empty."""
    from app.services.liquidacion_service import liquidacion_service

    inc_id = await _make_incapacidad(db_session, "LIQUIDACION")

    with pytest.raises(BadRequestException):
        await liquidacion_service.devolver_a_auditoria(
            db=db_session,
            incapacidad_id=inc_id,
            observacion="",
            liquidador_id=uuid4(),
        )


# ---------------------------------------------------------------------------
# 2. Devolution fails when incapacidad is not in LIQUIDACION / LIQUIDACION_PARCIAL
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_devolucion_desde_estado_invalido(db_session):
    """InvalidStateException when incapacidad is in EN_AUDITORIA."""
    from app.services.liquidacion_service import liquidacion_service

    inc_id = await _make_incapacidad(db_session, "EN_AUDITORIA")

    with pytest.raises(InvalidStateException):
        await liquidacion_service.devolver_a_auditoria(
            db=db_session,
            incapacidad_id=inc_id,
            observacion="Datos incorrectos",
            liquidador_id=uuid4(),
        )


# ---------------------------------------------------------------------------
# 3. Devolution from LIQUIDACION → EN_AUDITORIA
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_devolucion_exitosa_desde_liquidacion(db_session):
    """Successful devolution: LIQUIDACION → EN_AUDITORIA."""
    from app.services.liquidacion_service import liquidacion_service

    inc_id = await _make_incapacidad(db_session, "LIQUIDACION")
    liquidador_id = await _make_liquidador(db_session)

    incapacidad = await liquidacion_service.devolver_a_auditoria(
        db=db_session,
        incapacidad_id=inc_id,
        observacion="El IBL registrado no coincide con el reporte de nómina",
        liquidador_id=liquidador_id,
    )

    assert incapacidad.estado == EstadoIncapacidad.EN_AUDITORIA


# ---------------------------------------------------------------------------
# 4. Devolution from LIQUIDACION_PARCIAL → EN_AUDITORIA
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_devolucion_exitosa_desde_liquidacion_parcial(db_session):
    """Successful devolution: LIQUIDACION_PARCIAL → EN_AUDITORIA."""
    from app.services.liquidacion_service import liquidacion_service

    inc_id = await _make_incapacidad(db_session, "LIQUIDACION_PARCIAL")
    liquidador_id = await _make_liquidador(db_session)

    incapacidad = await liquidacion_service.devolver_a_auditoria(
        db=db_session,
        incapacidad_id=inc_id,
        observacion="Días aprobados no corresponden al diagnóstico",
        liquidador_id=liquidador_id,
    )

    assert incapacidad.estado == EstadoIncapacidad.EN_AUDITORIA


# ---------------------------------------------------------------------------
# 5. guardar_liquidacion creates a record
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_guardar_liquidacion_crea_registro(db_session):
    """guardar_liquidacion creates a Liquidacion row in the DB."""
    from app.services.liquidacion_service import liquidacion_service
    from app.schemas.liquidacion import LiquidacionGuardar

    inc_id = await _make_incapacidad(db_session, "LIQUIDACION")
    liquidador_id = await _make_liquidador(db_session)

    payload = LiquidacionGuardar(
        dias_autorizados=10,
        fecha_inicio_autorizada=date(2026, 1, 1),
        fecha_fin_autorizada=date(2026, 1, 10),
        ibl=Decimal("3500000.00"),
        notas_liquidador="Prueba de creación",
    )

    liq = await liquidacion_service.guardar_liquidacion(
        db=db_session,
        incapacidad_id=inc_id,
        data=payload,
        liquidador_id=liquidador_id,
    )

    assert liq is not None
    assert liq.incapacidad_id == inc_id
    assert liq.ibl == Decimal("3500000.00")
    assert liq.dias_autorizados == 10
    assert str(liq.liquidador_id) == str(liquidador_id)


# ---------------------------------------------------------------------------
# 6. guardar_liquidacion updates existing record (no duplicate)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_guardar_liquidacion_actualiza_registro(db_session):
    """Second call to guardar_liquidacion updates instead of inserting duplicate."""
    from app.services.liquidacion_service import liquidacion_service
    from app.schemas.liquidacion import LiquidacionGuardar

    inc_id = await _make_incapacidad(db_session, "LIQUIDACION")
    liquidador_id = await _make_liquidador(db_session)

    base_payload = LiquidacionGuardar(
        dias_autorizados=10,
        fecha_inicio_autorizada=date(2026, 1, 1),
        fecha_fin_autorizada=date(2026, 1, 10),
        ibl=Decimal("3500000.00"),
    )
    await liquidacion_service.guardar_liquidacion(
        db=db_session,
        incapacidad_id=inc_id,
        data=base_payload,
        liquidador_id=liquidador_id,
    )

    updated_payload = LiquidacionGuardar(
        dias_autorizados=10,
        fecha_inicio_autorizada=date(2026, 1, 1),
        fecha_fin_autorizada=date(2026, 1, 10),
        ibl=Decimal("4000000.00"),
        notas_liquidador="Valor IBL corregido",
    )
    liq2 = await liquidacion_service.guardar_liquidacion(
        db=db_session,
        incapacidad_id=inc_id,
        data=updated_payload,
        liquidador_id=liquidador_id,
    )

    assert liq2.ibl == Decimal("4000000.00")
    assert liq2.notas_liquidador == "Valor IBL corregido"

    # Only one row in the DB
    count_row = await db_session.execute(
        sa.text("SELECT COUNT(*) FROM liquidacion WHERE incapacidad_id = :id"),
        {"id": str(inc_id)},
    )
    assert count_row.scalar() == 1


# ---------------------------------------------------------------------------
# 7. guardar_liquidacion fails for wrong state
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_guardar_liquidacion_estado_invalido(db_session):
    """InvalidStateException when incapacidad is not in LIQUIDACION/LIQUIDACION_PARCIAL."""
    from app.services.liquidacion_service import liquidacion_service
    from app.schemas.liquidacion import LiquidacionGuardar

    inc_id = await _make_incapacidad(db_session, "EN_AUDITORIA")
    liquidador_id = await _make_liquidador(db_session)

    payload = LiquidacionGuardar(
        dias_autorizados=5,
        fecha_inicio_autorizada=date(2026, 1, 1),
        fecha_fin_autorizada=date(2026, 1, 5),
    )

    with pytest.raises(InvalidStateException):
        await liquidacion_service.guardar_liquidacion(
            db=db_session,
            incapacidad_id=inc_id,
            data=payload,
            liquidador_id=liquidador_id,
        )


# ---------------------------------------------------------------------------
# 8. get_liquidacion raises NotFoundException when not found
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_liquidacion_not_found(db_session):
    """NotFoundException when no liquidacion exists for the incapacidad."""
    from app.services.liquidacion_service import liquidacion_service

    inc_id = await _make_incapacidad(db_session, "LIQUIDACION")

    with pytest.raises(NotFoundException):
        await liquidacion_service.get_liquidacion(db_session, inc_id)


# ---------------------------------------------------------------------------
# 9. calcular_ibl_stub always returns ibl=None
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_calcular_ibl_stub_retorna_null(db_session):
    """calcular_ibl_stub returns ibl=None with informative nota."""
    from app.services.liquidacion_service import liquidacion_service

    inc_id = await _make_incapacidad(db_session, "LIQUIDACION")

    result = await liquidacion_service.calcular_ibl_stub(db_session, inc_id)

    assert result["ibl"] is None
    assert "Imaginex" in result["nota"]


# ---------------------------------------------------------------------------
# 10. _calcular_breakdown placeholder — all values None
# ---------------------------------------------------------------------------

def test_calcular_breakdown_placeholder_all_none():
    """_calcular_breakdown returns all None values while C1 is pending."""
    from app.services.liquidacion_service import _calcular_breakdown

    result = _calcular_breakdown(Decimal("3500000"), 10)

    for key, value in result.items():
        assert value is None, f"Expected None for {key}, got {value}"


# ---------------------------------------------------------------------------
# 11. calcular_breakdown with ibl=None returns None for all breakdown fields
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_calcular_breakdown_ibl_none(db_session):
    """When ibl=None, calcular_breakdown returns None for all breakdown values."""
    from app.services.liquidacion_service import liquidacion_service

    inc_id = await _make_incapacidad(db_session, "LIQUIDACION")

    result = await liquidacion_service.calcular_breakdown(
        db=db_session,
        incapacidad_id=inc_id,
        ibl=None,
        dias=10,
    )

    assert result["ibl"] is None
    assert result["dias"] == 10
    assert result["incapacidad_temporal"] is None
    assert "nota" in result


# ---------------------------------------------------------------------------
# 12. completar_liquidacion: LIQUIDACION → PAGADA
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_completar_liquidacion_a_pagada(db_session):
    """completar_liquidacion transitions LIQUIDACION → PAGADA."""
    from app.services.liquidacion_service import liquidacion_service

    inc_id = await _make_incapacidad(db_session, "LIQUIDACION")
    liquidador_id = await _make_liquidador(db_session)
    await _make_liquidacion_row(db_session, inc_id)

    incapacidad = await liquidacion_service.completar_liquidacion(
        db=db_session,
        incapacidad_id=inc_id,
        liquidador_id=liquidador_id,
    )

    assert incapacidad.estado == EstadoIncapacidad.PAGADA


# ---------------------------------------------------------------------------
# 13. completar_liquidacion: LIQUIDACION_PARCIAL → PAGADA_PARCIAL
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_completar_liquidacion_a_pagada_parcial(db_session):
    """completar_liquidacion transitions LIQUIDACION_PARCIAL → PAGADA_PARCIAL."""
    from app.services.liquidacion_service import liquidacion_service

    inc_id = await _make_incapacidad(db_session, "LIQUIDACION_PARCIAL")
    liquidador_id = await _make_liquidador(db_session)
    await _make_liquidacion_row(db_session, inc_id)

    incapacidad = await liquidacion_service.completar_liquidacion(
        db=db_session,
        incapacidad_id=inc_id,
        liquidador_id=liquidador_id,
    )

    assert incapacidad.estado == EstadoIncapacidad.PAGADA_PARCIAL


# ---------------------------------------------------------------------------
# 14. completar_liquidacion fails if no liquidacion record exists
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_completar_liquidacion_sin_registro(db_session):
    """NotFoundException when completar_liquidacion called without a saved liquidacion."""
    from app.services.liquidacion_service import liquidacion_service

    inc_id = await _make_incapacidad(db_session, "LIQUIDACION")
    liquidador_id = await _make_liquidador(db_session)

    with pytest.raises(NotFoundException):
        await liquidacion_service.completar_liquidacion(
            db=db_session,
            incapacidad_id=inc_id,
            liquidador_id=liquidador_id,
        )
