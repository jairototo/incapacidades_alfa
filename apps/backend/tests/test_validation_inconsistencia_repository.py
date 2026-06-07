"""
Tests de integración para ValidationInconsistenciaRepository.
Requiere base de datos de test con tablas pre_incapacidad y validation_inconsistencia.
"""
from datetime import date, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.validation_inconsistencia_repository import ValidationInconsistenciaRepository
from app.models.pre_incapacidad import PreIncapacidad
from app.schemas.validation_inconsistencia import ValidationInconsistenciaCreate


@pytest.fixture
async def pre_incapacidad(db_session: AsyncSession) -> PreIncapacidad:
    """Crea una pre-incapacidad mínima para usar como FK."""
    pre_inc = PreIncapacidad(
        estado="PENDIENTE",
        solicitante_correo="test@example.com",
        solicitante_nombres="Juan",
        empleado_tipo_documento="CC",
        empleado_numero_documento="1234567890",
        empleado_nombres="Carlos",
        tipo="ARL",
        tipo_enfermedad="ACCIDENTE_TRABAJO",
        fecha_inicio=date.today(),
        fecha_fin=date.today() + timedelta(days=5),
        dias_totales=5,
        diagnostico_cie10="M54.5",
        nombre_medico="Dr. García",
        registro_medico="12345",
    )
    db_session.add(pre_inc)
    await db_session.commit()
    await db_session.refresh(pre_inc)
    return pre_inc


@pytest.mark.asyncio
async def test_create_persists_record(db_session: AsyncSession, pre_incapacidad: PreIncapacidad):
    """create() debe persistir el registro y retornarlo con ID asignado."""
    repo = ValidationInconsistenciaRepository(db_session)
    schema = ValidationInconsistenciaCreate(
        pre_incapacidad_id=pre_incapacidad.id,
        categoria="FRAUD_ALERT",
        severidad="ERROR",
        codigo="EMPRESA_NOT_FOUND",
        descripcion="Empresa no encontrada en BD",
        campo_afectado="empresa_nit",
        valor_encontrado="900000001",
    )

    issue = await repo.create(schema)
    await db_session.commit()

    assert issue.id is not None
    assert issue.pre_incapacidad_id == pre_incapacidad.id
    assert issue.categoria == "FRAUD_ALERT"
    assert issue.severidad == "ERROR"
    assert issue.codigo == "EMPRESA_NOT_FOUND"
    assert issue.campo_afectado == "empresa_nit"
    assert issue.valor_encontrado == "900000001"


@pytest.mark.asyncio
async def test_get_by_pre_incapacidad_returns_all(db_session: AsyncSession, pre_incapacidad: PreIncapacidad):
    """get_by_pre_incapacidad() debe retornar todos los issues de esa pre-incapacidad."""
    repo = ValidationInconsistenciaRepository(db_session)

    for codigo in ("ISSUE_A", "ISSUE_B", "ISSUE_C"):
        await repo.create(ValidationInconsistenciaCreate(
            pre_incapacidad_id=pre_incapacidad.id,
            categoria="FIELD_VALIDATION",
            severidad="WARNING",
            codigo=codigo,
            descripcion=f"Descripción de {codigo}",
        ))
    await db_session.commit()

    issues = await repo.get_by_pre_incapacidad(pre_incapacidad.id)

    assert len(issues) == 3
    codigos = {i.codigo for i in issues}
    assert codigos == {"ISSUE_A", "ISSUE_B", "ISSUE_C"}


@pytest.mark.asyncio
async def test_get_by_pre_incapacidad_empty_for_unknown_id(db_session: AsyncSession):
    """get_by_pre_incapacidad() debe retornar lista vacía para ID inexistente."""
    repo = ValidationInconsistenciaRepository(db_session)
    issues = await repo.get_by_pre_incapacidad(uuid4())
    assert issues == []


@pytest.mark.asyncio
async def test_count_by_severidad_correct_counts(db_session: AsyncSession, pre_incapacidad: PreIncapacidad):
    """count_by_severidad() debe retornar conteos correctos por severidad."""
    repo = ValidationInconsistenciaRepository(db_session)

    await repo.create(ValidationInconsistenciaCreate(
        pre_incapacidad_id=pre_incapacidad.id,
        categoria="FRAUD_ALERT", severidad="ERROR", codigo="ERR_1", descripcion="Error 1",
    ))
    await repo.create(ValidationInconsistenciaCreate(
        pre_incapacidad_id=pre_incapacidad.id,
        categoria="FRAUD_ALERT", severidad="ERROR", codigo="ERR_2", descripcion="Error 2",
    ))
    await repo.create(ValidationInconsistenciaCreate(
        pre_incapacidad_id=pre_incapacidad.id,
        categoria="BUSINESS_RULE", severidad="WARNING", codigo="WARN_1", descripcion="Warning 1",
    ))
    await repo.create(ValidationInconsistenciaCreate(
        pre_incapacidad_id=pre_incapacidad.id,
        categoria="BUSINESS_RULE", severidad="INFO", codigo="INFO_1", descripcion="Info 1",
    ))
    await db_session.commit()

    counts = await repo.count_by_severidad(pre_incapacidad.id)

    assert counts["ERROR"] == 2
    assert counts["WARNING"] == 1
    assert counts["INFO"] == 1
    assert counts["total"] == 4


@pytest.mark.asyncio
async def test_count_by_severidad_zero_for_unknown_id(db_session: AsyncSession):
    """count_by_severidad() debe retornar todos en cero para ID sin issues."""
    repo = ValidationInconsistenciaRepository(db_session)
    counts = await repo.count_by_severidad(uuid4())

    assert counts["ERROR"] == 0
    assert counts["WARNING"] == 0
    assert counts["INFO"] == 0
    assert counts["total"] == 0


@pytest.mark.asyncio
async def test_has_errors_true_when_errors_exist(db_session: AsyncSession, pre_incapacidad: PreIncapacidad):
    """has_errors() debe retornar True cuando hay al menos un ERROR."""
    repo = ValidationInconsistenciaRepository(db_session)

    await repo.create(ValidationInconsistenciaCreate(
        pre_incapacidad_id=pre_incapacidad.id,
        categoria="FRAUD_ALERT", severidad="ERROR", codigo="ERR_X", descripcion="Error",
    ))
    await db_session.commit()

    assert await repo.has_errors(pre_incapacidad.id) is True


@pytest.mark.asyncio
async def test_has_errors_false_when_only_warnings(db_session: AsyncSession, pre_incapacidad: PreIncapacidad):
    """has_errors() debe retornar False si solo existen WARNING/INFO."""
    repo = ValidationInconsistenciaRepository(db_session)

    await repo.create(ValidationInconsistenciaCreate(
        pre_incapacidad_id=pre_incapacidad.id,
        categoria="BUSINESS_RULE", severidad="WARNING", codigo="WARN_X", descripcion="Warning",
    ))
    await db_session.commit()

    assert await repo.has_errors(pre_incapacidad.id) is False


@pytest.mark.asyncio
async def test_has_errors_false_when_no_issues(db_session: AsyncSession):
    """has_errors() debe retornar False cuando no hay issues."""
    repo = ValidationInconsistenciaRepository(db_session)
    assert await repo.has_errors(uuid4()) is False


@pytest.mark.asyncio
async def test_has_errors_handles_multiple_rows(db_session: AsyncSession, pre_incapacidad: PreIncapacidad):
    """has_errors() no debe fallar cuando existen múltiples filas ERROR (regresión)."""
    repo = ValidationInconsistenciaRepository(db_session)

    for i in range(5):
        await repo.create(ValidationInconsistenciaCreate(
            pre_incapacidad_id=pre_incapacidad.id,
            categoria="FRAUD_ALERT", severidad="ERROR",
            codigo=f"ERR_{i}", descripcion=f"Error {i}",
        ))
    await db_session.commit()

    # Debe retornar True sin lanzar "Multiple rows were found"
    assert await repo.has_errors(pre_incapacidad.id) is True
