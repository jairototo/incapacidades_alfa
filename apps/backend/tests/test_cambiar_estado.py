"""
Tests for Task 8.1: _cambiar_estado() centralized helper + mandatory observacion.

All state transitions must:
1. Pass through _cambiar_estado().
2. Reject empty / whitespace-only observaciones with BadRequestException("obligatoria").
3. Write a historial entry for every successful transition.
"""
import pytest
from datetime import date, datetime
from decimal import Decimal

from app.core.exceptions import BadRequestException
from app.utils.enums import TipoIncapacidad, EstadoIncapacidad, Prioridad


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
async def inc_radicada(db_session, test_empleado, test_empresa):
    """Incapacidad in RADICADA state."""
    from app.models.incapacidad import Incapacidad

    inc = Incapacidad(
        numero="INC-CS-RADICADA-001",
        empleado_id=test_empleado.id,
        empresa_id=test_empresa.id,
        tipo=TipoIncapacidad.ARL,
        fecha_inicio=date(2026, 2, 1),
        fecha_fin=date(2026, 2, 10),
        dias_totales=10,
        diagnostico_cie10="M545",
        descripcion_diagnostico="Prueba cambiar_estado",
        valor_dia=Decimal("100000.00"),
        valor_total=Decimal("1000000.00"),
        estado=EstadoIncapacidad.RADICADA,
        fecha_radicacion=datetime.utcnow(),
        prioridad=Prioridad.NORMAL,
    )
    db_session.add(inc)
    await db_session.commit()
    await db_session.refresh(inc)
    return inc


@pytest.fixture
async def inc_en_auditoria(db_session, test_empleado, test_empresa):
    """Incapacidad in EN_AUDITORIA state."""
    from app.models.incapacidad import Incapacidad

    inc = Incapacidad(
        numero="INC-CS-AUDITORIA-001",
        empleado_id=test_empleado.id,
        empresa_id=test_empresa.id,
        tipo=TipoIncapacidad.ARL,
        fecha_inicio=date(2026, 2, 1),
        fecha_fin=date(2026, 2, 10),
        dias_totales=10,
        diagnostico_cie10="M545",
        descripcion_diagnostico="Prueba cambiar_estado auditoria",
        valor_dia=Decimal("100000.00"),
        valor_total=Decimal("1000000.00"),
        estado=EstadoIncapacidad.EN_AUDITORIA,
        fecha_radicacion=datetime.utcnow(),
        prioridad=Prioridad.NORMAL,
    )
    db_session.add(inc)
    await db_session.commit()
    await db_session.refresh(inc)
    return inc


@pytest.fixture
async def inc_pendiente(db_session, test_empleado, test_empresa):
    """Incapacidad in PENDIENTE state."""
    from app.models.incapacidad import Incapacidad

    inc = Incapacidad(
        numero="INC-CS-PENDIENTE-001",
        empleado_id=test_empleado.id,
        empresa_id=test_empresa.id,
        tipo=TipoIncapacidad.ARL,
        fecha_inicio=date(2026, 2, 1),
        fecha_fin=date(2026, 2, 10),
        dias_totales=10,
        diagnostico_cie10="M545",
        descripcion_diagnostico="Prueba cambiar_estado pendiente",
        valor_dia=Decimal("100000.00"),
        valor_total=Decimal("1000000.00"),
        estado=EstadoIncapacidad.PENDIENTE,
        fecha_radicacion=datetime.utcnow(),
        pendiente_desde=datetime.utcnow(),
        prioridad=Prioridad.NORMAL,
    )
    db_session.add(inc)
    await db_session.commit()
    await db_session.refresh(inc)
    return inc


# ---------------------------------------------------------------------------
# Test: radicar_incapacidad requires non-empty observacion
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_radicar_requires_observacion(db_session, inc_radicada):
    """radicar_incapacidad with empty observacion must raise BadRequestException."""
    from app.services.incapacidad_service import incapacidad_service

    with pytest.raises(BadRequestException, match="obligatoria"):
        await incapacidad_service.radicar_incapacidad(
            db=db_session,
            incapacidad_id=inc_radicada.id,
            usuario_id=None,
            observacion="",  # empty — must be rejected
        )


@pytest.mark.asyncio
async def test_radicar_rejects_whitespace_observacion(db_session, inc_radicada):
    """radicar_incapacidad with whitespace-only observacion must raise BadRequestException."""
    from app.services.incapacidad_service import incapacidad_service

    with pytest.raises(BadRequestException, match="obligatoria"):
        await incapacidad_service.radicar_incapacidad(
            db=db_session,
            incapacidad_id=inc_radicada.id,
            usuario_id=None,
            observacion="   ",  # whitespace only — must be rejected
        )


@pytest.mark.asyncio
async def test_radicar_succeeds_with_observacion(db_session, inc_radicada):
    """radicar_incapacidad with valid observacion transitions to EN_AUDITORIA."""
    from app.services.incapacidad_service import incapacidad_service

    result = await incapacidad_service.radicar_incapacidad(
        db=db_session,
        incapacidad_id=inc_radicada.id,
        usuario_id=None,
        observacion="Radicación manual de prueba",
    )
    assert result.estado == EstadoIncapacidad.EN_AUDITORIA


# ---------------------------------------------------------------------------
# Test: retornar_a_auditoria requires non-empty observacion
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_retornar_a_auditoria_requires_observacion(db_session, inc_pendiente):
    """retornar_a_auditoria with empty observacion must raise BadRequestException."""
    from app.services.incapacidad_service import incapacidad_service

    with pytest.raises(BadRequestException, match="obligatoria"):
        await incapacidad_service.retornar_a_auditoria(
            db=db_session,
            incapacidad_id=inc_pendiente.id,
            observaciones="",  # empty — must be rejected
        )


@pytest.mark.asyncio
async def test_retornar_a_auditoria_rejects_whitespace(db_session, inc_pendiente):
    """retornar_a_auditoria with whitespace-only observacion must raise BadRequestException."""
    from app.services.incapacidad_service import incapacidad_service

    with pytest.raises(BadRequestException, match="obligatoria"):
        await incapacidad_service.retornar_a_auditoria(
            db=db_session,
            incapacidad_id=inc_pendiente.id,
            observaciones="   ",
        )


@pytest.mark.asyncio
async def test_retornar_a_auditoria_succeeds(db_session, inc_pendiente):
    """retornar_a_auditoria with valid observacion transitions to EN_AUDITORIA."""
    from app.services.incapacidad_service import incapacidad_service

    result = await incapacidad_service.retornar_a_auditoria(
        db=db_session,
        incapacidad_id=inc_pendiente.id,
        observaciones="Documentos recibidos, retomando auditoría",
    )
    assert result.estado == EstadoIncapacidad.EN_AUDITORIA
    assert result.pendiente_desde is None


# ---------------------------------------------------------------------------
# Test: auditar_incapacidad requires non-empty observacion for all actions
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_auditar_requires_observacion_solicitar_informacion(db_session, inc_en_auditoria):
    """auditar_incapacidad SOLICITAR_INFORMACION with empty observation must raise."""
    from app.services.incapacidad_service import incapacidad_service

    with pytest.raises(BadRequestException, match="obligatoria"):
        await incapacidad_service.auditar_incapacidad(
            db=db_session,
            incapacidad_id=inc_en_auditoria.id,
            accion="SOLICITAR_INFORMACION",
            observaciones="",
        )


@pytest.mark.asyncio
async def test_auditar_requires_observacion_rechazar(db_session, inc_en_auditoria):
    """auditar_incapacidad RECHAZAR with whitespace-only observation must raise."""
    from app.services.incapacidad_service import incapacidad_service

    with pytest.raises(BadRequestException, match="obligatoria"):
        await incapacidad_service.auditar_incapacidad(
            db=db_session,
            incapacidad_id=inc_en_auditoria.id,
            accion="RECHAZAR",
            observaciones="   ",
        )


# ---------------------------------------------------------------------------
# Test: _cambiar_estado writes historial entry on every successful transition
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_radicar_writes_historial_entry(db_session, inc_radicada):
    """radicar_incapacidad must write a historial entry with the observacion."""
    from app.services.incapacidad_service import incapacidad_service
    from app.services.historial_estado_service import historial_estado_service

    obs = "Radicación de prueba para historial"
    await incapacidad_service.radicar_incapacidad(
        db=db_session,
        incapacidad_id=inc_radicada.id,
        usuario_id=None,
        observacion=obs,
    )

    historial = await historial_estado_service.get_incapacidad_history(
        db=db_session,
        incapacidad_id=inc_radicada.id,
    )

    # The trigger writes the RADICADA entry; radicar_incapacidad writes the EN_AUDITORIA entry.
    en_auditoria_entries = [h for h in historial if h.estado_nuevo == "EN_AUDITORIA"]
    assert len(en_auditoria_entries) >= 1
    assert en_auditoria_entries[0].observacion == obs


@pytest.mark.asyncio
async def test_retornar_a_auditoria_writes_historial_entry(db_session, inc_pendiente):
    """retornar_a_auditoria must write a historial entry."""
    from app.services.incapacidad_service import incapacidad_service
    from app.services.historial_estado_service import historial_estado_service

    obs = "Documentación entregada"
    await incapacidad_service.retornar_a_auditoria(
        db=db_session,
        incapacidad_id=inc_pendiente.id,
        observaciones=obs,
    )

    historial = await historial_estado_service.get_incapacidad_history(
        db=db_session,
        incapacidad_id=inc_pendiente.id,
    )

    en_auditoria_entries = [h for h in historial if h.estado_nuevo == "EN_AUDITORIA"]
    assert len(en_auditoria_entries) >= 1
    assert obs in en_auditoria_entries[0].observacion


# ---------------------------------------------------------------------------
# Test: rechazar_incapacidad (direct) requires non-empty motivo via _cambiar_estado
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_rechazar_rejects_empty_motivo(db_session, inc_en_auditoria):
    """rechazar_incapacidad with empty motivo must raise BadRequestException."""
    from app.services.incapacidad_service import incapacidad_service

    with pytest.raises(BadRequestException, match="obligatoria"):
        await incapacidad_service.rechazar_incapacidad(
            db=db_session,
            incapacidad_id=inc_en_auditoria.id,
            motivo="",  # empty — _cambiar_estado must reject
        )


@pytest.mark.asyncio
async def test_rechazar_rejects_whitespace_motivo(db_session, inc_en_auditoria):
    """rechazar_incapacidad with whitespace-only motivo must raise BadRequestException."""
    from app.services.incapacidad_service import incapacidad_service

    with pytest.raises(BadRequestException, match="obligatoria"):
        await incapacidad_service.rechazar_incapacidad(
            db=db_session,
            incapacidad_id=inc_en_auditoria.id,
            motivo="   ",
        )
