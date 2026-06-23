"""
TDD tests for Task 3.0: CREACION_SINIESTRO state — ADMINISTRADOR links external siniestro.

Tests:
1. iniciar_creacion_siniestro sets state to CREACION_SINIESTRO and saves numero_siniestro
2. iniciar_creacion_siniestro raises BadRequestException for non-ARL incapacidad
3. iniciar_creacion_siniestro raises BadRequestException when observacion is empty
4. _vincular_siniestro_async creates local siniestro and transitions to EN_AUDITORIA
"""
import pytest
from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

from app.core.exceptions import BadRequestException
from app.utils.enums import TipoIncapacidad, EstadoIncapacidad, Prioridad


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def incapacidad_en_auditoria(db_session, test_empleado, test_empresa):
    """ARL incapacidad in EN_AUDITORIA state."""
    from app.models.incapacidad import Incapacidad

    inc = Incapacidad(
        numero="INC-ARL-SIN-001",
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
async def incapacidad_salud_en_auditoria(db_session, test_afiliado):
    """SALUD incapacidad in EN_AUDITORIA — should NOT accept CREACION_SINIESTRO."""
    from app.models.incapacidad import Incapacidad

    inc = Incapacidad(
        numero="INC-SAL-SIN-001",
        afiliado_id=test_afiliado.id,
        tipo=TipoIncapacidad.SALUD,
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
async def incapacidad_creacion_siniestro(db_session, test_empleado, test_empresa):
    """ARL incapacidad already in CREACION_SINIESTRO state with numero_siniestro set."""
    from app.models.incapacidad import Incapacidad

    inc = Incapacidad(
        numero="INC-ARL-SIN-002",
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
        estado=EstadoIncapacidad.CREACION_SINIESTRO,
        numero_siniestro="SINX-2026-001",
        fecha_radicacion=datetime.utcnow(),
        prioridad=Prioridad.NORMAL,
    )
    db_session.add(inc)
    await db_session.commit()
    await db_session.refresh(inc)
    return inc


# ---------------------------------------------------------------------------
# Service tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_iniciar_creacion_siniestro_sets_state(
    db_session, incapacidad_en_auditoria, test_usuario
):
    """iniciar_creacion_siniestro must transition to CREACION_SINIESTRO and set numero_siniestro."""
    from app.services.incapacidad_service import incapacidad_service

    result = await incapacidad_service.iniciar_creacion_siniestro(
        db=db_session,
        incapacidad_id=incapacidad_en_auditoria.id,
        numero_siniestro_externo="SINX-2026-001",
        usuario_id=test_usuario.id,
        observacion="Vinculando siniestro externo SINX-2026-001",
    )

    assert result.estado == EstadoIncapacidad.CREACION_SINIESTRO
    assert result.numero_siniestro == "SINX-2026-001"


@pytest.mark.asyncio
async def test_iniciar_creacion_siniestro_rejects_salud(
    db_session, incapacidad_salud_en_auditoria, test_usuario
):
    """iniciar_creacion_siniestro must raise BadRequestException for SALUD incapacidades."""
    from app.services.incapacidad_service import incapacidad_service

    with pytest.raises(BadRequestException, match="ARL"):
        await incapacidad_service.iniciar_creacion_siniestro(
            db=db_session,
            incapacidad_id=incapacidad_salud_en_auditoria.id,
            numero_siniestro_externo="SINX-2026-001",
            usuario_id=test_usuario.id,
            observacion="Intentando crear siniestro en SALUD",
        )


@pytest.mark.asyncio
async def test_iniciar_creacion_siniestro_requires_observacion(
    db_session, incapacidad_en_auditoria, test_usuario
):
    """iniciar_creacion_siniestro must raise BadRequestException when observacion is empty."""
    from app.services.incapacidad_service import incapacidad_service

    with pytest.raises(BadRequestException, match="observaci"):
        await incapacidad_service.iniciar_creacion_siniestro(
            db=db_session,
            incapacidad_id=incapacidad_en_auditoria.id,
            numero_siniestro_externo="SINX-2026-001",
            usuario_id=test_usuario.id,
            observacion="",
        )


# ---------------------------------------------------------------------------
# Celery task async function tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_vincular_siniestro_task_transitions_to_en_auditoria(
    db_session, incapacidad_creacion_siniestro
):
    """
    _vincular_en_session must create a Siniestro, link it, and transition to EN_AUDITORIA.
    """
    from app.tasks.siniestro_tasks import _vincular_en_session

    result = await _vincular_en_session(
        db=db_session,
        incapacidad_id=incapacidad_creacion_siniestro.id,
        numero_siniestro="SINX-2026-001",
    )

    assert result["status"] == "success"

    await db_session.refresh(incapacidad_creacion_siniestro)
    assert incapacidad_creacion_siniestro.estado == EstadoIncapacidad.EN_AUDITORIA
    assert incapacidad_creacion_siniestro.siniestro_id is not None


@pytest.mark.asyncio
async def test_vincular_siniestro_task_skips_wrong_state(
    db_session, incapacidad_en_auditoria
):
    """
    _vincular_en_session must skip (idempotent) if incapacidad is no longer in CREACION_SINIESTRO.
    """
    from app.tasks.siniestro_tasks import _vincular_en_session

    result = await _vincular_en_session(
        db=db_session,
        incapacidad_id=incapacidad_en_auditoria.id,
        numero_siniestro="SINX-2026-001",
    )

    assert result["status"] == "skipped"


@pytest.mark.asyncio
async def test_vincular_siniestro_reuses_existing_siniestro(
    db_session, incapacidad_creacion_siniestro, test_empleado, test_empresa
):
    """
    _vincular_en_session must reuse an existing Siniestro if numero_siniestro matches.
    """
    from app.models.siniestro import Siniestro
    from app.utils.enums import TipoSiniestro, GravedadSiniestro, SyncSource, EstadoSiniestro
    from app.tasks.siniestro_tasks import _vincular_en_session
    from datetime import datetime

    # Pre-create the siniestro
    existing = Siniestro(
        numero_siniestro="SINX-2026-001",
        empleado_id=test_empleado.id,
        empresa_id=test_empresa.id,
        fecha_siniestro=date(2026, 1, 1),
        tipo_siniestro=TipoSiniestro.ACCIDENTE_TRABAJO,
        descripcion="Siniestro preexistente",
        gravedad=GravedadSiniestro.LEVE,
        estado=EstadoSiniestro.REPORTADO,
        sync_source=SyncSource.MANUAL,
        fecha_reporte=datetime.utcnow(),
    )
    db_session.add(existing)
    await db_session.commit()
    await db_session.refresh(existing)

    result = await _vincular_en_session(
        db=db_session,
        incapacidad_id=incapacidad_creacion_siniestro.id,
        numero_siniestro="SINX-2026-001",
    )

    assert result["status"] == "success"
    assert result["siniestro_id"] == str(existing.id)

    await db_session.refresh(incapacidad_creacion_siniestro)
    assert incapacidad_creacion_siniestro.siniestro_id == existing.id
