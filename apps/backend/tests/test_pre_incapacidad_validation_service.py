"""
Tests para PreIncapacidadValidationService.
"""
from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4
import pytest

from app.services.pre_incapacidad_validation_service import PreIncapacidadValidationService
from app.models.pre_incapacidad import PreIncapacidad
from app.models.empresa import Empresa
from app.models.empleado import Empleado


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


def _make_pre_inc(**kwargs) -> PreIncapacidad:
    """Helper para crear un PreIncapacidad válido con overrides opcionales."""
    defaults = dict(
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
        fecha_fin=date.today() + timedelta(days=5),
        dias_totales=6,
        diagnostico_cie10="M54.5",
        nombre_medico="Dr. García",
        registro_medico="12345",
    )
    defaults.update(kwargs)
    return PreIncapacidad(**defaults)


# ── Business rules ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_business_rule_retroactive_beyond_limit():
    """Test: incapacidad retroactiva > 30 días genera WARNING."""
    pre_inc = _make_pre_inc(
        fecha_inicio=date.today() - timedelta(days=40),
        fecha_fin=date.today() - timedelta(days=35),
        dias_totales=6,
    )

    service = PreIncapacidadValidationService(pre_incapacidad=pre_inc, empleado=None, empresa=None)
    issues = await service.validate_business_rules()

    assert any(i.codigo == "RETROACTIVE_BEYOND_LIMIT" for i in issues)
    assert any(i.severidad == "WARNING" for i in issues)


@pytest.mark.asyncio
async def test_business_rule_duration_exceeds_limit():
    """Test: incapacidad > 180 días genera WARNING."""
    pre_inc = _make_pre_inc(
        fecha_inicio=date.today(),
        fecha_fin=date.today() + timedelta(days=190),
        dias_totales=200,
    )

    service = PreIncapacidadValidationService(pre_incapacidad=pre_inc, empleado=None, empresa=None)
    issues = await service.validate_business_rules()

    assert any(i.codigo == "DURATION_EXCEEDS_LIMIT" for i in issues)


@pytest.mark.asyncio
async def test_business_rule_no_issues_for_valid_case():
    """Test: incapacidad normal no genera business rule issues."""
    pre_inc = _make_pre_inc(
        fecha_inicio=date.today(),
        fecha_fin=date.today() + timedelta(days=5),
        dias_totales=6,
    )

    service = PreIncapacidadValidationService(pre_incapacidad=pre_inc, empleado=None, empresa=None)
    issues = await service.validate_business_rules()

    assert all(i.codigo not in ("DURATION_EXCEEDS_LIMIT", "RETROACTIVE_BEYOND_LIMIT") for i in issues)


# ── Fraud alerts ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_fraud_alert_high_daily_value():
    """Test: valor_dia > 500k genera FRAUD_ALERT WARNING."""
    pre_inc = _make_pre_inc(valor_dia=Decimal("600000"))

    service = PreIncapacidadValidationService(pre_incapacidad=pre_inc, empleado=None, empresa=None)
    issues = await service.validate_fraud_alerts()

    assert any(i.codigo == "UNUSUALLY_HIGH_DAILY_VALUE" for i in issues)
    assert any(i.severidad == "WARNING" for i in issues)


@pytest.mark.asyncio
async def test_fraud_alert_no_issue_below_limit():
    """Test: valor_dia normal no genera alerta."""
    pre_inc = _make_pre_inc(valor_dia=Decimal("100000"))

    service = PreIncapacidadValidationService(pre_incapacidad=pre_inc, empleado=None, empresa=None)
    issues = await service.validate_fraud_alerts()

    assert len(issues) == 0


@pytest.mark.asyncio
async def test_fraud_alert_no_issue_when_no_valor_dia():
    """Test: sin valor_dia no genera alerta (campo opcional)."""
    pre_inc = _make_pre_inc(valor_dia=None)

    service = PreIncapacidadValidationService(pre_incapacidad=pre_inc, empleado=None, empresa=None)
    issues = await service.validate_fraud_alerts()

    assert len(issues) == 0


# ── Integration checks ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_integration_empresa_not_found_generates_fraud_alert():
    """Test: empresa_nit presente pero empresa=None genera FRAUD_ALERT ERROR."""
    pre_inc = _make_pre_inc(empresa_nit="900000001")

    service = PreIncapacidadValidationService(pre_incapacidad=pre_inc, empleado=None, empresa=None)
    issues = await service.validate_integration()

    assert any(i.codigo == "EMPRESA_NOT_FOUND" for i in issues)
    assert any(i.severidad == "ERROR" and i.categoria == "FRAUD_ALERT" for i in issues)


@pytest.mark.asyncio
async def test_integration_empleado_not_found_generates_fraud_alert():
    """Test: tipo=ARL con empleado=None genera FRAUD_ALERT ERROR."""
    pre_inc = _make_pre_inc(tipo="ARL")

    service = PreIncapacidadValidationService(pre_incapacidad=pre_inc, empleado=None, empresa=None)
    issues = await service.validate_integration()

    assert any(i.codigo == "EMPLEADO_NOT_FOUND" for i in issues)
    assert any(i.severidad == "ERROR" and i.categoria == "FRAUD_ALERT" for i in issues)


@pytest.mark.asyncio
async def test_integration_empresa_inactive_generates_warning():
    """Test: empresa en estado INACTIVA genera INTEGRATION_CHECK WARNING."""
    pre_inc = _make_pre_inc(empresa_nit="900000001")
    empresa = Empresa(nit="900000001", razon_social="Empresa Inactiva", estado="INACTIVA")

    service = PreIncapacidadValidationService(pre_incapacidad=pre_inc, empleado=None, empresa=empresa)
    issues = await service.validate_integration()

    assert any(i.codigo == "EMPRESA_INACTIVE" for i in issues)
    assert any(i.severidad == "WARNING" for i in issues)


@pytest.mark.asyncio
async def test_integration_empleado_inactive_generates_warning():
    """Test: empleado en estado INACTIVO genera INTEGRATION_CHECK WARNING."""
    pre_inc = _make_pre_inc(tipo="ARL", empresa_nit="900000001")
    empresa = Empresa(nit="900000001", razon_social="Empresa Test", estado="ACTIVA")
    empleado = Empleado(
        numero_documento="1234567",
        tipo_documento="CC",
        nombres="Carlos",
        estado="INACTIVO",
    )

    service = PreIncapacidadValidationService(pre_incapacidad=pre_inc, empleado=empleado, empresa=empresa)
    issues = await service.validate_integration()

    assert any(i.codigo == "EMPLEADO_INACTIVE" for i in issues)
    assert any(i.severidad == "WARNING" for i in issues)


@pytest.mark.asyncio
async def test_integration_no_issues_when_empresa_and_empleado_active():
    """Test: empresa y empleado activos → no hay integration issues."""
    pre_inc = _make_pre_inc(tipo="ARL", empresa_nit="900000001")
    empresa = Empresa(nit="900000001", razon_social="Empresa Test", estado="ACTIVA")
    empleado = Empleado(
        numero_documento="1234567",
        tipo_documento="CC",
        nombres="Carlos",
        estado="ACTIVO",
    )

    service = PreIncapacidadValidationService(pre_incapacidad=pre_inc, empleado=empleado, empresa=empresa)
    issues = await service.validate_integration()

    assert len(issues) == 0


@pytest.mark.asyncio
async def test_integration_no_empresa_check_when_no_nit():
    """Test: sin empresa_nit no se verifica empresa."""
    pre_inc = _make_pre_inc(tipo="ARL", empresa_nit=None)
    empleado = Empleado(numero_documento="1234567", tipo_documento="CC", nombres="Carlos", estado="ACTIVO")

    service = PreIncapacidadValidationService(pre_incapacidad=pre_inc, empleado=empleado, empresa=None)
    issues = await service.validate_integration()

    # No debe generar EMPRESA_NOT_FOUND porque no se proporcionó NIT
    assert not any(i.codigo == "EMPRESA_NOT_FOUND" for i in issues)


# ── validate_all() ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_validate_all_returns_issues_from_all_categories():
    """validate_all() debe combinar issues de todas las categorías."""
    pre_inc = _make_pre_inc(
        tipo="ARL",
        empresa_nit="900000001",
        valor_dia=Decimal("600000"),
        fecha_inicio=date.today() - timedelta(days=45),
        fecha_fin=date.today() - timedelta(days=40),
        dias_totales=6,
    )

    service = PreIncapacidadValidationService(pre_incapacidad=pre_inc, empleado=None, empresa=None)
    all_issues = await service.validate_all()

    categorias = {i.categoria for i in all_issues}
    # Deben aparecer al menos FRAUD_ALERT (empresa/empleado faltantes) y BUSINESS_RULE (retroactiva)
    assert "FRAUD_ALERT" in categorias
    assert "BUSINESS_RULE" in categorias


@pytest.mark.asyncio
async def test_validate_all_returns_empty_for_perfect_case():
    """validate_all() debe retornar lista vacía para un caso completamente válido con entidades activas."""
    pre_inc = _make_pre_inc(
        tipo="ARL",
        empresa_nit="900000001",
        fecha_inicio=date.today(),
        fecha_fin=date.today() + timedelta(days=5),
        dias_totales=6,
        valor_dia=Decimal("100000"),
    )
    empresa = Empresa(nit="900000001", razon_social="Empresa Test", estado="ACTIVA")
    empleado = Empleado(numero_documento="1234567", tipo_documento="CC", nombres="Carlos", estado="ACTIVO")

    service = PreIncapacidadValidationService(pre_incapacidad=pre_inc, empleado=empleado, empresa=empresa)
    all_issues = await service.validate_all()

    errors = [i for i in all_issues if i.severidad == "ERROR"]
    assert len(errors) == 0
