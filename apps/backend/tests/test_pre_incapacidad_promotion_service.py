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

from sqlalchemy import select, func

from app.db.repositories.validation_inconsistencia_repository import ValidationInconsistenciaRepository
from app.models.pre_incapacidad import PreIncapacidad
from app.models.pre_documento import PreDocumento
from app.models.documento import Documento
from app.models.incapacidad import Incapacidad
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
    """Pre-incapacidad con NIT de empresa inexistente → debe generar INTEGRATION_CHECK WARNING."""
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
async def test_promote_empresa_not_found_still_creates_incapacidad(
    db_session: AsyncSession, pre_inc_sin_empresa: PreIncapacidad
):
    """Pre-incapacidad con empresa inexistente debe quedar PROCESADA con INTEGRATION_CHECK persistido."""
    service = PromotePreIncapacidadService(db_session)
    result = await service.promote_pre_incapacidad(pre_inc_sin_empresa.id)

    assert result.success is True

    # Verificar estado en BD — ahora PROCESADA, no RECHAZADA
    await db_session.refresh(pre_inc_sin_empresa)
    assert pre_inc_sin_empresa.estado == "PROCESADA"

    # Verificar que los issues fueron persistidos como INTEGRATION_CHECK WARNING
    val_repo = ValidationInconsistenciaRepository(db_session)
    issues = await val_repo.get_by_pre_incapacidad(pre_inc_sin_empresa.id)
    assert len(issues) > 0
    assert any(i.codigo == "EMPRESA_NOT_FOUND" for i in issues)
    assert any(i.categoria == "INTEGRATION_CHECK" for i in issues)


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
    # EMPRESA_NOT_FOUND y EMPLEADO_NOT_FOUND son ahora WARNING (no ERROR)
    assert summary.warnings >= 1  # al menos EMPRESA_NOT_FOUND
    assert summary.errors == 0


@pytest.mark.asyncio
async def test_promote_first_call_succeeds_and_marks_procesada(
    db_session: AsyncSession, pre_inc_sin_empresa: PreIncapacidad
):
    """Primera llamada a promote con empresa inexistente crea incapacidad y marca PROCESADA."""
    service = PromotePreIncapacidadService(db_session)
    result = await service.promote_pre_incapacidad(pre_inc_sin_empresa.id)
    assert result.success is True
    await db_session.refresh(pre_inc_sin_empresa)
    assert pre_inc_sin_empresa.estado == "PROCESADA"
    assert pre_inc_sin_empresa.incapacidad_id is not None


@pytest.mark.asyncio
async def test_promote_second_call_is_noop(
    db_session: AsyncSession, pre_inc_sin_empresa: PreIncapacidad
):
    """Segunda llamada a promote no crea una segunda Incapacidad (idempotency guard)."""
    service = PromotePreIncapacidadService(db_session)
    result1 = await service.promote_pre_incapacidad(pre_inc_sin_empresa.id)
    assert result1.success is True

    # Count total incapacidad rows before the second call
    count_before = (
        await db_session.execute(
            select(func.count()).select_from(Incapacidad).where(
                Incapacidad.id == result1.incapacidad_id
            )
        )
    ).scalar_one()
    assert count_before == 1

    result2 = await service.promote_pre_incapacidad(pre_inc_sin_empresa.id)
    assert result2.success is True
    assert result2.incapacidad_id == result1.incapacidad_id

    # Still exactly one Incapacidad row after second call
    count_after = (
        await db_session.execute(
            select(func.count()).select_from(Incapacidad).where(
                Incapacidad.id == result1.incapacidad_id
            )
        )
    ).scalar_one()
    assert count_after == 1

    # Estado remains PROCESADA
    await db_session.refresh(pre_inc_sin_empresa)
    assert pre_inc_sin_empresa.estado == "PROCESADA"


@pytest.mark.asyncio
async def test_promote_skips_when_incapacidad_id_set(
    db_session: AsyncSession, pre_inc_sin_empresa: PreIncapacidad
):
    """Guard actúa cuando incapacidad_id ya está asignado aunque estado no sea PROCESADA.

    Simula crash parcial: incapacidad_id fue enlazado pero estado no se actualizó a PROCESADA.
    Una segunda llamada no debe crear una nueva Incapacidad.
    """
    service = PromotePreIncapacidadService(db_session)

    # First promotion sets both incapacidad_id and estado=PROCESADA
    result1 = await service.promote_pre_incapacidad(pre_inc_sin_empresa.id)
    assert result1.success is True
    first_incapacidad_id = result1.incapacidad_id

    # Simulate partial crash: reset estado to PENDIENTE, leave incapacidad_id set
    await db_session.refresh(pre_inc_sin_empresa)
    pre_inc_sin_empresa.estado = "PENDIENTE"
    db_session.add(pre_inc_sin_empresa)
    await db_session.commit()
    await db_session.refresh(pre_inc_sin_empresa)
    assert pre_inc_sin_empresa.incapacidad_id == first_incapacidad_id
    assert pre_inc_sin_empresa.estado == "PENDIENTE"

    # Second call should hit the guard (incapacidad_id is not None) and not create a new row
    result2 = await service.promote_pre_incapacidad(pre_inc_sin_empresa.id)
    assert result2.success is True
    assert result2.incapacidad_id == first_incapacidad_id

    # Confirm no second Incapacidad was created
    all_inc_count = (
        await db_session.execute(
            select(func.count()).select_from(Incapacidad).where(
                Incapacidad.id == first_incapacidad_id
            )
        )
    ).scalar_one()
    assert all_inc_count == 1


@pytest.fixture
async def pre_inc_con_documentos(
    db_session: AsyncSession, empresa_activa: Empresa, empleado_activo: Empleado
) -> PreIncapacidad:
    """Pre-incapacidad válida con dos documentos adjuntos (uno OK, uno ERROR)."""
    pre_inc = PreIncapacidad(
        estado="PENDIENTE",
        solicitante_correo="docs@example.com",
        solicitante_nombres="Ana",
        empleado_tipo_documento="CC",
        empleado_numero_documento=empleado_activo.numero_documento,
        empleado_nombres=empleado_activo.nombres,
        tipo="ARL",
        tipo_enfermedad="ACCIDENTE_TRABAJO",
        fecha_inicio=date.today(),
        fecha_fin=date.today() + timedelta(days=3),
        dias_totales=4,
        diagnostico_cie10="S52.0",
        nombre_medico="Dr. Ruiz",
        registro_medico="REG-003",
        empresa_nit=empresa_activa.nit,
        empresa_nombre=empresa_activa.razon_social,
    )
    db_session.add(pre_inc)
    await db_session.flush()

    doc_ok = PreDocumento(
        pre_incapacidad_id=pre_inc.id,
        tipo_documento="INCAPACIDAD_MEDICA",
        nombre_original="incapacidad.pdf",
        ruta_storage="pre-incapacidades/incapacidad.pdf",
        bucket="docs",
        mime_type="application/pdf",
        tamanio_bytes=102400,
        estado_subida="OK",
    )
    doc_adicional = PreDocumento(
        pre_incapacidad_id=pre_inc.id,
        tipo_documento="SOPORTE_ADICIONAL",
        nombre_original="soporte.jpg",
        ruta_storage="pre-incapacidades/soporte.jpg",
        bucket="docs",
        mime_type="image/jpeg",
        tamanio_bytes=51200,
        estado_subida="OK",
    )
    doc_error = PreDocumento(
        pre_incapacidad_id=pre_inc.id,
        tipo_documento="HISTORIA_CLINICA",
        nombre_original="historia_fallida.pdf",
        ruta_storage="pre-incapacidades/historia_fallida.pdf",
        bucket="docs",
        mime_type="application/pdf",
        tamanio_bytes=20480,
        estado_subida="ERROR",
    )
    db_session.add_all([doc_ok, doc_adicional, doc_error])
    await db_session.commit()
    await db_session.refresh(pre_inc)
    return pre_inc


@pytest.mark.asyncio
async def test_promote_copies_ok_documents_to_incapacidad(
    db_session: AsyncSession, pre_inc_con_documentos: PreIncapacidad
):
    """Documentos con estado_subida=OK deben copiarse al incapacidad creado."""
    service = PromotePreIncapacidadService(db_session)
    result = await service.promote_pre_incapacidad(pre_inc_con_documentos.id)

    assert result.success is True
    assert result.incapacidad_id is not None

    docs = (
        await db_session.execute(
            select(Documento).where(Documento.incapacidad_id == result.incapacidad_id)
        )
    ).scalars().all()

    assert len(docs) == 2  # doc_ok + doc_adicional (doc_error excluded)
    nombres = {d.nombre_original for d in docs}
    assert "incapacidad.pdf" in nombres
    assert "soporte.jpg" in nombres
    assert "historia_fallida.pdf" not in nombres


@pytest.mark.asyncio
async def test_promote_maps_soporte_adicional_to_otros(
    db_session: AsyncSession, pre_inc_con_documentos: PreIncapacidad
):
    """SOPORTE_ADICIONAL en PreDocumento debe mapearse a OTROS en Documento."""
    service = PromotePreIncapacidadService(db_session)
    result = await service.promote_pre_incapacidad(pre_inc_con_documentos.id)

    docs = (
        await db_session.execute(
            select(Documento).where(Documento.incapacidad_id == result.incapacidad_id)
        )
    ).scalars().all()

    tipos = {d.tipo_documento for d in docs}
    assert "INCAPACIDAD_MEDICA" in tipos
    assert "OTROS" in tipos


@pytest.mark.asyncio
async def test_promote_no_documents_does_not_fail(
    db_session: AsyncSession, pre_inc_valida: PreIncapacidad
):
    """La promoción sin documentos adjuntos debe completarse sin error."""
    service = PromotePreIncapacidadService(db_session)
    result = await service.promote_pre_incapacidad(pre_inc_valida.id)

    assert result.success is True
    docs = (
        await db_session.execute(
            select(Documento).where(Documento.incapacidad_id == result.incapacidad_id)
        )
    ).scalars().all()
    assert len(docs) == 0
