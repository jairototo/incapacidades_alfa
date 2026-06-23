"""
TDD Tests for Task 2.1: pendiente_desde column + mandatory observation enforcement.

Tests:
1. PENDIENTE transition requires non-empty observation
2. PENDIENTE transition sets pendiente_desde
3. Leaving PENDIENTE (RETORNAR_A_AUDITORIA) clears pendiente_desde
"""
import pytest
from datetime import date, datetime
from decimal import Decimal

from app.core.exceptions import BadRequestException
from app.utils.enums import TipoIncapacidad, EstadoIncapacidad, Prioridad


@pytest.fixture
async def incapacidad_en_auditoria(db_session, test_empleado, test_empresa):
    """Incapacidad in EN_AUDITORIA state, ready to be audited."""
    from app.models.incapacidad import Incapacidad

    inc = Incapacidad(
        numero="INC-ARL-PEND-001",
        empleado_id=test_empleado.id,
        empresa_id=test_empresa.id,
        tipo=TipoIncapacidad.ARL,
        fecha_inicio=date(2026, 1, 1),
        fecha_fin=date(2026, 1, 10),
        dias_totales=10,
        diagnostico_cie10="M545",
        descripcion_diagnostico="Lumbago no especificado",
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
async def incapacidad_pendiente(db_session, test_empleado, test_empresa):
    """Incapacidad in PENDIENTE state with pendiente_desde set."""
    from app.models.incapacidad import Incapacidad

    inc = Incapacidad(
        numero="INC-ARL-PEND-002",
        empleado_id=test_empleado.id,
        empresa_id=test_empresa.id,
        tipo=TipoIncapacidad.ARL,
        fecha_inicio=date(2026, 1, 1),
        fecha_fin=date(2026, 1, 10),
        dias_totales=10,
        diagnostico_cie10="M545",
        descripcion_diagnostico="Lumbago no especificado",
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


@pytest.mark.asyncio
async def test_pendiente_requires_observation(db_session, incapacidad_en_auditoria):
    """SOLICITAR_INFORMACION with empty observation must raise BadRequestException."""
    from app.services.incapacidad_service import incapacidad_service
    with pytest.raises(BadRequestException, match="observaci"):
        await incapacidad_service.auditar_incapacidad(
            db=db_session,
            incapacidad_id=incapacidad_en_auditoria.id,
            accion="SOLICITAR_INFORMACION",
            observaciones="",  # empty — must be rejected
        )


@pytest.mark.asyncio
async def test_pendiente_sets_pendiente_desde(db_session, incapacidad_en_auditoria):
    """SOLICITAR_INFORMACION with valid observation sets pendiente_desde."""
    from app.services.incapacidad_service import incapacidad_service
    result = await incapacidad_service.auditar_incapacidad(
        db=db_session,
        incapacidad_id=incapacidad_en_auditoria.id,
        accion="SOLICITAR_INFORMACION",
        observaciones="Falta la historia clínica del evento",
    )
    assert result.pendiente_desde is not None


@pytest.mark.asyncio
async def test_leaving_pendiente_clears_pendiente_desde(db_session, incapacidad_pendiente):
    """RETORNAR_A_AUDITORIA clears pendiente_desde and returns to EN_AUDITORIA."""
    from app.services.incapacidad_service import incapacidad_service
    result = await incapacidad_service.retornar_a_auditoria(
        db=db_session,
        incapacidad_id=incapacidad_pendiente.id,
        observaciones="Documentos recibidos, retomando auditoría",
    )
    assert result.pendiente_desde is None
    assert result.estado == EstadoIncapacidad.EN_AUDITORIA


@pytest.mark.asyncio
async def test_all_audit_actions_require_observation(db_session, incapacidad_en_auditoria):
    """ALL audit actions must reject empty observation strings."""
    from app.services.incapacidad_service import incapacidad_service
    acciones = ["RECHAZAR", "APROBAR_PARA_PAGO", "CREACION_SINIESTRO"]
    for accion in acciones:
        with pytest.raises(BadRequestException, match="observaci"):
            await incapacidad_service.auditar_incapacidad(
                db=db_session,
                incapacidad_id=incapacidad_en_auditoria.id,
                accion=accion,
                observaciones="   ",  # whitespace only — must be rejected
            )
