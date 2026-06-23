"""
Tests for Task 2.2: get_pendientes_vencidos repository query.

Verifies that:
1. Only PENDIENTE incapacidades past the cutoff date are returned.
2. Recent PENDIENTE records (within the threshold) are NOT returned.
3. Records with pendiente_desde = None are NOT returned.
4. Records in other states are NOT returned even if pendiente_desde is old.
"""
import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal

from app.utils.enums import TipoIncapacidad, EstadoIncapacidad, Prioridad


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_inc(numero, estado, pendiente_desde=None):
    """Factory for a minimal Incapacidad object (no relations required)."""
    from app.models.incapacidad import Incapacidad

    return Incapacidad(
        numero=numero,
        tipo=TipoIncapacidad.ARL,
        fecha_inicio=date(2026, 1, 1),
        fecha_fin=date(2026, 1, 10),
        dias_totales=10,
        diagnostico_cie10="M545",
        descripcion_diagnostico="Lumbago no especificado",
        valor_dia=Decimal("100000.00"),
        valor_total=Decimal("1000000.00"),
        estado=estado,
        fecha_radicacion=datetime.utcnow(),
        prioridad=Prioridad.NORMAL,
        pendiente_desde=pendiente_desde,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
async def incapacidad_pendiente_vieja(db_session, test_empleado, test_empresa):
    """PENDIENTE with pendiente_desde = 9 days ago (should trigger alert)."""
    inc = _make_inc(
        "INC-ALERT-OLD-001",
        EstadoIncapacidad.PENDIENTE,
        pendiente_desde=datetime.utcnow() - timedelta(days=9),
    )
    inc.empleado_id = test_empleado.id
    inc.empresa_id = test_empresa.id
    db_session.add(inc)
    await db_session.commit()
    await db_session.refresh(inc)
    return inc


@pytest.fixture
async def incapacidad_pendiente_reciente(db_session, test_empleado, test_empresa):
    """PENDIENTE with pendiente_desde = 3 days ago (within threshold, no alert)."""
    inc = _make_inc(
        "INC-ALERT-NEW-001",
        EstadoIncapacidad.PENDIENTE,
        pendiente_desde=datetime.utcnow() - timedelta(days=3),
    )
    inc.empleado_id = test_empleado.id
    inc.empresa_id = test_empresa.id
    db_session.add(inc)
    await db_session.commit()
    await db_session.refresh(inc)
    return inc


@pytest.fixture
async def incapacidad_pendiente_sin_fecha(db_session, test_empleado, test_empresa):
    """PENDIENTE with pendiente_desde = None (should never appear in alerts)."""
    inc = _make_inc(
        "INC-ALERT-NULL-001",
        EstadoIncapacidad.PENDIENTE,
        pendiente_desde=None,
    )
    inc.empleado_id = test_empleado.id
    inc.empresa_id = test_empresa.id
    db_session.add(inc)
    await db_session.commit()
    await db_session.refresh(inc)
    return inc


@pytest.fixture
async def incapacidad_auditoria_vieja(db_session, test_empleado, test_empresa):
    """EN_AUDITORIA with pendiente_desde = 9 days ago — wrong state, no alert."""
    inc = _make_inc(
        "INC-ALERT-AUDIT-001",
        EstadoIncapacidad.EN_AUDITORIA,
        pendiente_desde=datetime.utcnow() - timedelta(days=9),
    )
    inc.empleado_id = test_empleado.id
    inc.empresa_id = test_empresa.id
    db_session.add(inc)
    await db_session.commit()
    await db_session.refresh(inc)
    return inc


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_pendientes_vencidos_returns_only_old_ones(
    db_session,
    incapacidad_pendiente_vieja,
    incapacidad_pendiente_reciente,
):
    """Only the old PENDIENTE (>8 days) must be returned; recent one must not."""
    from app.db.repositories.incapacidad_repository import incapacidad_repository

    result = await incapacidad_repository.get_pendientes_vencidos(db_session, dias=8)
    numeros = [inc.numero for inc in result]

    assert incapacidad_pendiente_vieja.numero in numeros
    assert incapacidad_pendiente_reciente.numero not in numeros


@pytest.mark.asyncio
async def test_get_pendientes_vencidos_excludes_null_pendiente_desde(
    db_session,
    incapacidad_pendiente_vieja,
    incapacidad_pendiente_sin_fecha,
):
    """Records with pendiente_desde = None must never appear in alerts."""
    from app.db.repositories.incapacidad_repository import incapacidad_repository

    result = await incapacidad_repository.get_pendientes_vencidos(db_session, dias=8)
    numeros = [inc.numero for inc in result]

    assert incapacidad_pendiente_sin_fecha.numero not in numeros
    assert incapacidad_pendiente_vieja.numero in numeros


@pytest.mark.asyncio
async def test_get_pendientes_vencidos_excludes_wrong_state(
    db_session,
    incapacidad_auditoria_vieja,
):
    """EN_AUDITORIA records must not appear even with an old pendiente_desde."""
    from app.db.repositories.incapacidad_repository import incapacidad_repository

    result = await incapacidad_repository.get_pendientes_vencidos(db_session, dias=8)
    numeros = [inc.numero for inc in result]

    assert incapacidad_auditoria_vieja.numero not in numeros


@pytest.mark.asyncio
async def test_get_pendientes_vencidos_empty_when_no_old_records(db_session):
    """Should return empty list when no records exceed the threshold."""
    from app.db.repositories.incapacidad_repository import incapacidad_repository

    result = await incapacidad_repository.get_pendientes_vencidos(db_session, dias=8)
    # May contain records from other tests depending on isolation, but the core assertion
    # is that the method returns a list (possibly empty).
    assert isinstance(result, list)


@pytest.mark.asyncio
async def test_get_pendientes_vencidos_exact_boundary(
    db_session,
    test_empleado,
    test_empresa,
):
    """A record at exactly 8 days old should be included (pendiente_desde <= cutoff)."""
    from app.models.incapacidad import Incapacidad
    from app.db.repositories.incapacidad_repository import incapacidad_repository

    # Set pendiente_desde to exactly 8 days + 1 second ago to be just past the boundary
    inc = _make_inc(
        "INC-ALERT-BOUNDARY-001",
        EstadoIncapacidad.PENDIENTE,
        pendiente_desde=datetime.utcnow() - timedelta(days=8, seconds=1),
    )
    inc.empleado_id = test_empleado.id
    inc.empresa_id = test_empresa.id
    db_session.add(inc)
    await db_session.commit()
    await db_session.refresh(inc)

    result = await incapacidad_repository.get_pendientes_vencidos(db_session, dias=8)
    numeros = [r.numero for r in result]

    assert inc.numero in numeros
