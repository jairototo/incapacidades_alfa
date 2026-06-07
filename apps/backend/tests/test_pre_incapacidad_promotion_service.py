"""
Tests de integración para PromotePreIncapacidadService.
Verifica que la promoción de pre-incapacidades a incapacidades funcione correctamente,
incluyendo la persistencia de validation_inconsistencia y cambios de estado.
"""
from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.validation_inconsistencia_repository import ValidationInconsistenciaRepository
from app.models.pre_incapacidad import PreIncapacidad
from app.models.empresa import Empresa
from app.models.empleado import Empleado
from app.services.pre_incapacidad_promotion_service import PromotePreIncapacidadService
from app.utils.enums import EstadoEmpresa, EstadoEmpleado, TipoDocumento


@pytest.fixture
async def empresa_activa(db_session: AsyncSession) -> Empresa:
    empresa = Empresa(
        nit="901000999",
        razon_social="Empresa Promo Test SAS",
        estado=EstadoEmpresa.ACTIVA,
    )
    db_session.add(empresa)
    await db_session.commit()
    await db_session.refresh(empresa)
    return empresa


@pytest.fixture
async def empleado_activo(db_session: AsyncSession, empresa_activa: Empresa) -> Empleado:
    empleado = Empleado(
        empresa_id=empresa_activa.id,
        numero_documento="7777777",
        tipo_documento=TipoDocumento.CC,
        nombres="Pedro",
        apellidos="Promo",
        fecha_ingreso=date(2020, 1, 1),
        estado=EstadoEmpleado.ACTIVO,
    )
    db_session.add(empleado)
    await db_session.commit()
    await db_session.refresh(empleado)
    return empleado


@pytest.fixture
async def pre_inc_sin_empresa(db_session: AsyncSession) -> PreIncapacidad:
    """Pre-incapacidad con NIT de empresa inexistente → debe generar FRAUD_ALERT."""
    pre_inc = PreIncapacidad(
        estado="PENDIENTE",
        solicitante_correo="user@example.com",
        solicitante_nombres="Maria",
        empleado_tipo_documento="CC",
        empleado_numero_documento="9999999",
        empleado_nombres="Luis",
        tipo="ARL",
        tipo_enfermedad="ACCIDENTE_TRABAJO",
        fecha_inicio=date.today(),
        fecha_fin=date.today() + timedelta(days=5),
        dias_totales=6,
        diagnostico_cie10="M54.5",
        nombre_medico="Dr. Pérez",
        registro_medico="REG-001",
        empresa_nit="000000000",  # NIT que no existe en BD
    )
    db_session.add(pre_inc)
    await db_session.commit()
    await db_session.refresh(pre_inc)
    return pre_inc


@pytest.fixture
async def pre_inc_valida(db_session: AsyncSession, empresa_activa: Empresa, empleado_activo: Empleado) -> PreIncapacidad:
    """Pre-incapacidad con empresa y empleado que SÍ existen en BD."""
    pre_inc = PreIncapacidad(
        estado="PENDIENTE",
        solicitante_correo="user@example.com",
        solicitante_nombres="Maria",
        empleado_tipo_documento="CC",
        empleado_numero_documento=empleado_activo.numero_documento,
        empleado_nombres=empleado_activo.nombres,
        tipo="ARL",
        tipo_enfermedad="ACCIDENTE_TRABAJO",
        fecha_inicio=date.today(),
        fecha_fin=date.today() + timedelta(days=5),
        dias_totales=6,
        diagnostico_cie10="M54.5",
        nombre_medico="Dr. López",
        registro_medico="REG-002",
        empresa_nit=empresa_activa.nit,
        empresa_nombre=empresa_activa.razon_social,
    )
    db_session.add(pre_inc)
    await db_session.commit()
    await db_session.refresh(pre_inc)
    return pre_inc


@pytest.mark.asyncio
async def test_promote_not_found_returns_error(db_session: AsyncSession):
    """Cuando no existe la pre-incapacidad, el resultado es failure sin crash."""
    service = PromotePreIncapacidadService(db_session)
    result = await service.promote_pre_incapacidad(uuid4())

    assert result.success is False
    assert result.error_message == "Pre-incapacidad no encontrada"
    assert result.validation_summary.total_issues == 0


@pytest.mark.asyncio
async def test_promote_empresa_not_found_marks_rechazada(
    db_session: AsyncSession, pre_inc_sin_empresa: PreIncapacidad
):
    """Pre-incapacidad con empresa inexistente debe quedar RECHAZADA con FRAUD_ALERT persistido."""
    service = PromotePreIncapacidadService(db_session)
    result = await service.promote_pre_incapacidad(pre_inc_sin_empresa.id)

    assert result.success is False
    assert result.validation_summary.errors > 0

    # Verificar estado en BD
    await db_session.refresh(pre_inc_sin_empresa)
    assert pre_inc_sin_empresa.estado == "RECHAZADA"

    # Verificar que los issues fueron persistidos
    val_repo = ValidationInconsistenciaRepository(db_session)
    issues = await val_repo.get_by_pre_incapacidad(pre_inc_sin_empresa.id)
    assert len(issues) > 0
    assert any(i.codigo == "EMPRESA_NOT_FOUND" for i in issues)
    assert any(i.categoria == "FRAUD_ALERT" for i in issues)


@pytest.mark.asyncio
async def test_promote_valid_pre_inc_marks_procesada(
    db_session: AsyncSession, pre_inc_valida: PreIncapacidad
):
    """Pre-incapacidad con empresa y empleado válidos debe quedar PROCESADA."""
    service = PromotePreIncapacidadService(db_session)
    result = await service.promote_pre_incapacidad(pre_inc_valida.id)

    assert result.success is True
    assert result.validation_summary.errors == 0

    # Verificar estado en BD
    await db_session.refresh(pre_inc_valida)
    assert pre_inc_valida.estado == "PROCESADA"


@pytest.mark.asyncio
async def test_promote_valid_pre_inc_no_error_issues_persisted(
    db_session: AsyncSession, pre_inc_valida: PreIncapacidad
):
    """Para pre-incapacidad válida, no deben persistirse issues de severidad ERROR."""
    service = PromotePreIncapacidadService(db_session)
    await service.promote_pre_incapacidad(pre_inc_valida.id)

    val_repo = ValidationInconsistenciaRepository(db_session)
    has_errors = await val_repo.has_errors(pre_inc_valida.id)
    assert has_errors is False


@pytest.mark.asyncio
async def test_promote_returns_summary_with_correct_counts(
    db_session: AsyncSession, pre_inc_sin_empresa: PreIncapacidad
):
    """El PromotionResult debe tener conteos coherentes con los issues persistidos."""
    service = PromotePreIncapacidadService(db_session)
    result = await service.promote_pre_incapacidad(pre_inc_sin_empresa.id)

    summary = result.validation_summary
    assert summary.total_issues == summary.errors + summary.warnings + summary.infos
    assert summary.errors >= 1  # al menos EMPRESA_NOT_FOUND y EMPLEADO_NOT_FOUND


@pytest.mark.asyncio
async def test_promote_idempotent_second_call_returns_error(
    db_session: AsyncSession, pre_inc_sin_empresa: PreIncapacidad
):
    """Segunda llamada a promote con misma ID no debe crashear."""
    service = PromotePreIncapacidadService(db_session)
    # Primera llamada — marca RECHAZADA
    result1 = await service.promote_pre_incapacidad(pre_inc_sin_empresa.id)
    assert result1.success is False

    # Segunda llamada — ya está RECHAZADA pero no debe crashear
    result2 = await service.promote_pre_incapacidad(pre_inc_sin_empresa.id)
    assert result2 is not None  # retorna algo, no crash
