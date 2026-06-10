"""
Tests para ValidationInconsistenciaRepository.
Cubre: create, get_by_pre_incapacidad, count_by_severidad, has_errors,
delete_by_pre_incapacidad, y get_by_incapacidad.
"""
from datetime import date, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.validation_inconsistencia_repository import ValidationInconsistenciaRepository
from app.models.pre_incapacidad import PreIncapacidad
from app.models.incapacidad import Incapacidad
from app.models.validation_inconsistencia import ValidationInconsistencia
from app.schemas.validation_inconsistencia import ValidationInconsistenciaCreate
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
        fecha_radicacion=datetime.utcnow(),
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


# ---------------------------------------------------------------------------
# create
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_stores_inconsistencia(db_session: AsyncSession):
    """create() persiste una ValidationInconsistencia y la retorna con id."""
    pre = await _make_pre_inc(db_session)
    await db_session.commit()

    repo = ValidationInconsistenciaRepository(db_session)
    schema = ValidationInconsistenciaCreate(
        pre_incapacidad_id=pre.id,
        categoria="BUSINESS_RULE",
        severidad="ERROR",
        codigo="TEST_CREATE",
        descripcion="Prueba de creación",
    )
    issue = await repo.create(schema)
    await db_session.commit()

    assert issue.id is not None
    assert issue.codigo == "TEST_CREATE"
    assert issue.severidad == "ERROR"
    assert issue.pre_incapacidad_id == pre.id


# ---------------------------------------------------------------------------
# get_by_pre_incapacidad
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_by_pre_incapacidad_returns_its_issues(db_session: AsyncSession):
    """get_by_pre_incapacidad retorna solo los issues de esa pre-incapacidad."""
    pre_a = await _make_pre_inc(db_session)
    pre_b = await _make_pre_inc(db_session)

    issue_a = ValidationInconsistencia(
        pre_incapacidad_id=pre_a.id,
        categoria="BUSINESS_RULE",
        severidad="WARNING",
        codigo="CODE_A",
        descripcion="A",
    )
    issue_b = ValidationInconsistencia(
        pre_incapacidad_id=pre_b.id,
        categoria="BUSINESS_RULE",
        severidad="ERROR",
        codigo="CODE_B",
        descripcion="B",
    )
    db_session.add_all([issue_a, issue_b])
    await db_session.commit()

    repo = ValidationInconsistenciaRepository(db_session)
    results = await repo.get_by_pre_incapacidad(pre_a.id)
    assert len(results) == 1
    assert results[0].codigo == "CODE_A"


@pytest.mark.asyncio
async def test_get_by_pre_incapacidad_empty(db_session: AsyncSession):
    """get_by_pre_incapacidad retorna lista vacía cuando no hay issues."""
    pre = await _make_pre_inc(db_session)
    await db_session.commit()

    repo = ValidationInconsistenciaRepository(db_session)
    results = await repo.get_by_pre_incapacidad(pre.id)
    assert results == []


# ---------------------------------------------------------------------------
# count_by_severidad
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_count_by_severidad(db_session: AsyncSession):
    """count_by_severidad devuelve conteos correctos por nivel."""
    pre = await _make_pre_inc(db_session)
    db_session.add_all([
        ValidationInconsistencia(
            pre_incapacidad_id=pre.id,
            categoria="BUSINESS_RULE",
            severidad="ERROR",
            codigo="E1",
            descripcion="error 1",
        ),
        ValidationInconsistencia(
            pre_incapacidad_id=pre.id,
            categoria="BUSINESS_RULE",
            severidad="ERROR",
            codigo="E2",
            descripcion="error 2",
        ),
        ValidationInconsistencia(
            pre_incapacidad_id=pre.id,
            categoria="INTEGRATION_CHECK",
            severidad="WARNING",
            codigo="W1",
            descripcion="warning 1",
        ),
    ])
    await db_session.commit()

    repo = ValidationInconsistenciaRepository(db_session)
    counts = await repo.count_by_severidad(pre.id)
    assert counts["ERROR"] == 2
    assert counts["WARNING"] == 1
    assert counts["total"] == 3


# ---------------------------------------------------------------------------
# has_errors
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_has_errors_true_when_errors_exist(db_session: AsyncSession):
    """has_errors retorna True cuando hay al menos un issue de severidad ERROR."""
    pre = await _make_pre_inc(db_session)
    db_session.add(ValidationInconsistencia(
        pre_incapacidad_id=pre.id,
        categoria="BUSINESS_RULE",
        severidad="ERROR",
        codigo="ERR_X",
        descripcion="error x",
    ))
    await db_session.commit()

    repo = ValidationInconsistenciaRepository(db_session)
    assert await repo.has_errors(pre.id) is True


@pytest.mark.asyncio
async def test_has_errors_false_when_only_warnings(db_session: AsyncSession):
    """has_errors retorna False cuando solo hay WARNINGs."""
    pre = await _make_pre_inc(db_session)
    db_session.add(ValidationInconsistencia(
        pre_incapacidad_id=pre.id,
        categoria="INTEGRATION_CHECK",
        severidad="WARNING",
        codigo="WARN_X",
        descripcion="warning x",
    ))
    await db_session.commit()

    repo = ValidationInconsistenciaRepository(db_session)
    assert await repo.has_errors(pre.id) is False


@pytest.mark.asyncio
async def test_has_errors_false_when_no_issues(db_session: AsyncSession):
    """has_errors retorna False cuando no hay issues."""
    pre = await _make_pre_inc(db_session)
    await db_session.commit()

    repo = ValidationInconsistenciaRepository(db_session)
    assert await repo.has_errors(pre.id) is False


# ---------------------------------------------------------------------------
# delete_by_pre_incapacidad
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_delete_by_pre_incapacidad_removes_all(db_session: AsyncSession):
    """delete_by_pre_incapacidad elimina todos los issues de la pre-incapacidad."""
    pre = await _make_pre_inc(db_session)
    db_session.add_all([
        ValidationInconsistencia(
            pre_incapacidad_id=pre.id,
            categoria="BUSINESS_RULE",
            severidad="ERROR",
            codigo="D1",
            descripcion="del 1",
        ),
        ValidationInconsistencia(
            pre_incapacidad_id=pre.id,
            categoria="BUSINESS_RULE",
            severidad="WARNING",
            codigo="D2",
            descripcion="del 2",
        ),
    ])
    await db_session.commit()

    repo = ValidationInconsistenciaRepository(db_session)
    deleted = await repo.delete_by_pre_incapacidad(pre.id)
    await db_session.commit()

    assert deleted == 2
    remaining = await repo.get_by_pre_incapacidad(pre.id)
    assert remaining == []


@pytest.mark.asyncio
async def test_delete_by_pre_incapacidad_returns_zero_when_none(db_session: AsyncSession):
    """delete_by_pre_incapacidad retorna 0 si no hay issues."""
    pre = await _make_pre_inc(db_session)
    await db_session.commit()

    repo = ValidationInconsistenciaRepository(db_session)
    deleted = await repo.delete_by_pre_incapacidad(pre.id)
    assert deleted == 0


# ---------------------------------------------------------------------------
# get_by_incapacidad
# ---------------------------------------------------------------------------

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
