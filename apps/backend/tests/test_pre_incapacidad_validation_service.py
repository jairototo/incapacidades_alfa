"""
Tests para PreIncapacidadValidationService.
"""
from datetime import date, timedelta
from uuid import uuid4
import pytest

from app.services.pre_incapacidad_validation_service import PreIncapacidadValidationService
from app.models.pre_incapacidad import PreIncapacidad


@pytest.mark.asyncio
async def test_field_validation_missing_required_fields():
    """Test: campo requerido vacío debe generar ERROR."""
    pre_inc = PreIncapacidad(
        id=uuid4(),
        numero_radicacion=202600001,
        estado="PENDIENTE",
        solicitante_correo="test@example.com",
        solicitante_nombres="Juan",
        empleado_tipo_documento="CC",
        empleado_numero_documento="",  # ← FALTA
        empleado_nombres="Carlos",
        tipo="ARL",
        tipo_enfermedad="ACCIDENTE_TRABAJO",
        fecha_inicio=date.today(),
        fecha_fin=date.today() + timedelta(days=3),
        dias_totales=3,
        diagnostico_cie10="M54.5",
        nombre_medico="Dr. García",
        registro_medico="12345",
    )

    service = PreIncapacidadValidationService(
        pre_incapacidad=pre_inc,
        empleado=None,
        empresa=None,
    )

    issues = await service.validate_field_level()

    assert len(issues) > 0
    assert any(i.codigo == "EMPTY_EMPLEADO_NUMERO" for i in issues)
    assert any(i.severidad == "ERROR" for i in issues)


@pytest.mark.asyncio
async def test_field_validation_invalid_date_range():
    """Test: fecha_fin < fecha_inicio debe generar ERROR."""
    pre_inc = PreIncapacidad(
        id=uuid4(),
        numero_radicacion=202600001,
        estado="PENDIENTE",
        solicitante_correo="test@example.com",
        solicitante_nombres="Juan",
        empleado_tipo_documento="CC",
        empleado_numero_documento="1234567",
        empleado_nombres="Carlos",
        tipo="ARL",
        tipo_enfermedad="ACCIDENTE_TRABAJO",
        fecha_inicio=date.today(),
        fecha_fin=date.today() - timedelta(days=1),
        dias_totales=-1,
        diagnostico_cie10="M54.5",
        nombre_medico="Dr. García",
        registro_medico="12345",
    )

    service = PreIncapacidadValidationService(
        pre_incapacidad=pre_inc,
        empleado=None,
        empresa=None,
    )

    issues = await service.validate_field_level()

    assert any(i.codigo == "INVALID_DATE_RANGE" for i in issues)


@pytest.mark.asyncio
async def test_business_rule_validation_dias_totales_mismatch():
    """Test: dias_totales no coincide con fecha_inicio/fin."""
    pre_inc = PreIncapacidad(
        id=uuid4(),
        numero_radicacion=202600001,
        estado="PENDIENTE",
        solicitante_correo="test@example.com",
        solicitante_nombres="Juan",
        empleado_tipo_documento="CC",
        empleado_numero_documento="1234567",
        empleado_nombres="Carlos",
        tipo="ARL",
        tipo_enfermedad="ACCIDENTE_TRABAJO",
        fecha_inicio=date(2024, 1, 1),
        fecha_fin=date(2024, 1, 10),
        dias_totales=5,
        diagnostico_cie10="M54.5",
        nombre_medico="Dr. García",
        registro_medico="12345",
    )

    service = PreIncapacidadValidationService(
        pre_incapacidad=pre_inc,
        empleado=None,
        empresa=None,
    )

    issues = await service.validate_business_rules()

    assert any(i.codigo == "DIAS_TOTALES_MISMATCH" for i in issues)


@pytest.mark.asyncio
async def test_complete_validation_all_categories():
    """Test: validar todas las categorías."""
    pre_inc = PreIncapacidad(
        id=uuid4(),
        numero_radicacion=202600001,
        estado="PENDIENTE",
        solicitante_correo="test@example.com",
        solicitante_nombres="Juan",
        empleado_tipo_documento="CC",
        empleado_numero_documento="1234567",
        empleado_nombres="Carlos",
        tipo="ARL",
        tipo_enfermedad="ACCIDENTE_TRABAJO",
        fecha_inicio=date.today(),
        fecha_fin=date.today() + timedelta(days=3),
        dias_totales=3,
        diagnostico_cie10="M54.5",
        nombre_medico="Dr. García",
        registro_medico="12345",
    )

    service = PreIncapacidadValidationService(
        pre_incapacidad=pre_inc,
        empleado=None,
        empresa=None,
    )

    all_issues = await service.validate_all()

    # Debe haber issues de integración
    assert len(all_issues) > 0
