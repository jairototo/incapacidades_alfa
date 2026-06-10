"""
Tests para ValidationInconsistenciaRepository.get_by_incapacidad.
Verifica que retorna issues tanto por incapacidad_id directo como
via pre_incapacidad.incapacidad_id.
"""
from datetime import date, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.validation_inconsistencia_repository import ValidationInconsistenciaRepository
from app.models.pre_incapacidad import PreIncapacidad
from app.models.incapacidad import Incapacidad
from app.models.validation_inconsistencia import ValidationInconsistencia
from app.utils.enums import TipoIncapacidad, EstadoIncapacidad, Prioridad


async def _make_incapacidad(db: AsyncSession) -> Incapacidad:
    inc = Incapacidad(
        numero=f"INC-TEST-{uuid4().hex[:8]}",
        tipo=TipoIncapacidad.ARL,
        estado=EstadoIncapacidad.EN_AUDITORIA,
        prioridad=Prioridad.NORMAL,
        fecha_inicio=date.today(),
        fecha_fin=date.today() + timedelta(days=5),
        dias_totales=6,
        fecha_radicacion=__import__('datetime').datetime.utcnow(),
    )
    db.add(inc)
    await db.flush()
    return inc


async def _make_pre_inc(db: AsyncSession, incapacidad_id=None) -> PreIncapacidad:
    pre = PreIncapacidad(
        estado="PROCESADA",
        solicitante_correo="x@x.com",
        solicitante_nombres="X",
        empleado_tipo_documento="CC",
        empleado_numero_documento="11111111",
        empleado_nombres="Test",
        tipo="ARL",
        tipo_enfermedad="ACCIDENTE_TRABAJO",
        fecha_inicio=date.today(),
        fecha_fin=date.today() + timedelta(days=5),
        dias_totales=6,
        diagnostico_cie10="M54.5",
        nombre_medico="Dr. X",
        registro_medico="REG-X",
        incapacidad_id=incapacidad_id,
    )
    db.add(pre)
    await db.flush()
    return pre


@pytest.mark.asyncio
async def test_get_by_incapacidad_direct_link(db_session: AsyncSession):
    """Issue con incapacidad_id directo debe aparecer."""
    inc = await _make_incapacidad(db_session)
    pre = await _make_pre_inc(db_session, incapacidad_id=inc.id)
    issue = ValidationInconsistencia(
        pre_incapacidad_id=pre.id,
        incapacidad_id=inc.id,
        categoria="BUSINESS_RULE",
        severidad="WARNING",
        codigo="TEST_CODE",
        descripcion="Test",
    )
    db_session.add(issue)
    await db_session.commit()

    repo = ValidationInconsistenciaRepository(db_session)
    results = await repo.get_by_incapacidad(inc.id)
    assert len(results) == 1
    assert results[0].codigo == "TEST_CODE"


@pytest.mark.asyncio
async def test_get_by_incapacidad_via_pre_incapacidad(db_session: AsyncSession):
    """Issue con solo pre_incapacidad_id debe aparecer si pre_inc apunta a la incapacidad."""
    inc = await _make_incapacidad(db_session)
    pre = await _make_pre_inc(db_session, incapacidad_id=inc.id)
    issue = ValidationInconsistencia(
        pre_incapacidad_id=pre.id,
        incapacidad_id=None,
        categoria="INTEGRATION_CHECK",
        severidad="WARNING",
        codigo="EMPRESA_NOT_FOUND",
        descripcion="Empresa no encontrada",
    )
    db_session.add(issue)
    await db_session.commit()

    repo = ValidationInconsistenciaRepository(db_session)
    results = await repo.get_by_incapacidad(inc.id)
    assert len(results) == 1
    assert results[0].codigo == "EMPRESA_NOT_FOUND"


@pytest.mark.asyncio
async def test_get_by_incapacidad_excludes_other(db_session: AsyncSession):
    """Issues de otra incapacidad no deben aparecer."""
    inc_a = await _make_incapacidad(db_session)
    inc_b = await _make_incapacidad(db_session)
    pre_b = await _make_pre_inc(db_session, incapacidad_id=inc_b.id)
    issue = ValidationInconsistencia(
        pre_incapacidad_id=pre_b.id,
        incapacidad_id=inc_b.id,
        categoria="FRAUD_ALERT",
        severidad="WARNING",
        codigo="POSSIBLE_DUPLICATE",
        descripcion="Duplicado",
    )
    db_session.add(issue)
    await db_session.commit()

    repo = ValidationInconsistenciaRepository(db_session)
    results = await repo.get_by_incapacidad(inc_a.id)
    assert len(results) == 0


@pytest.mark.asyncio
async def test_get_by_incapacidad_returns_both_sources(db_session: AsyncSession):
    """Debe retornar issues tanto de incapacidad_id directo como de pre_incapacidad."""
    inc = await _make_incapacidad(db_session)
    pre = await _make_pre_inc(db_session, incapacidad_id=inc.id)

    issue_pre = ValidationInconsistencia(
        pre_incapacidad_id=pre.id,
        incapacidad_id=None,
        categoria="INTEGRATION_CHECK",
        severidad="WARNING",
        codigo="EMPLEADO_NOT_FOUND",
        descripcion="Empleado no encontrado",
    )
    issue_direct = ValidationInconsistencia(
        pre_incapacidad_id=pre.id,
        incapacidad_id=inc.id,
        categoria="BUSINESS_RULE",
        severidad="WARNING",
        codigo="OVERLAPPING_PERIOD",
        descripcion="Periodo solapado",
    )
    db_session.add_all([issue_pre, issue_direct])
    await db_session.commit()

    repo = ValidationInconsistenciaRepository(db_session)
    results = await repo.get_by_incapacidad(inc.id)
    codigos = {r.codigo for r in results}
    assert "EMPLEADO_NOT_FOUND" in codigos
    assert "OVERLAPPING_PERIOD" in codigos
