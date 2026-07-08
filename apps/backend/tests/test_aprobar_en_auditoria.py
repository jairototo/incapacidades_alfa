"""
TDD tests for aprobar_en_auditoria service method.

Tests:
1. estado_invalido — InvalidStateException when not EN_AUDITORIA
2. observacion_corta — Pydantic validation error when observacion < 10 chars
3. fechas_invertidas — Pydantic validation error when fin < inicio
4. arl_sin_siniestro_error — ERROR rule SINIESTRO_REQUERIDO blocks approval
5. auditoria_resultado_persiste_en_error — rows written even when validation fails
6. aprobacion_completa_mismo_periodo — LIQUIDACION when dates match original
7. aprobacion_parcial_fechas_distintas — LIQUIDACION_PARCIAL when dates differ
8. texto_copiable_en_respuesta — response includes non-empty texto_copiable
9. plantilla_auditoria_creada — PlantillaAuditoria row saved after success
"""
import pytest
from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

from pydantic import ValidationError

from app.core.exceptions import BadRequestException, InvalidStateException
from app.utils.enums import TipoIncapacidad, EstadoIncapacidad, Prioridad
from app.schemas.incapacidad import AprobarAuditoriaRequest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_request(**overrides) -> AprobarAuditoriaRequest:
    defaults = dict(
        fecha_inicio_aprobada=date(2026, 1, 1),
        fecha_fin_aprobada=date(2026, 1, 10),
        canal_recepcion="Portal",
        observacion="Revisión completa, procede el pago",
    )
    defaults.update(overrides)
    return AprobarAuditoriaRequest(**defaults)


async def _make_incapacidad_en_auditoria(db_session, tipo=TipoIncapacidad.SALUD, siniestro_id=None):
    """Insert minimal EN_AUDITORIA incapacidad and return ORM object."""
    from app.models.incapacidad import Incapacidad
    from app.models.empleado import Empleado
    from app.models.empresa import Empresa
    from app.models.afiliado import Afiliado
    from app.utils.enums import EstadoAfiliado

    if tipo == TipoIncapacidad.ARL:
        empresa = Empresa(
            razon_social="EmpTest",
            nit=f"NIT-{uuid4().hex[:6]}",
        )
        db_session.add(empresa)
        await db_session.flush()

        empleado = Empleado(
            nombres="Juan",
            apellidos="Test",
            numero_documento=f"DOC{uuid4().hex[:6]}",
            tipo_documento="CC",
            empresa_id=empresa.id,
            fecha_ingreso=date(2020, 1, 1),
        )
        db_session.add(empleado)
        await db_session.flush()
        emp_id = empleado.id
        emp_empresa_id = empresa.id
        afiliado_id = None
    else:
        # SALUD incapacidades require afiliado_id (DB check constraint)
        afiliado = Afiliado(
            numero_poliza=f"POL-{uuid4().hex[:6]}",
            tipo_poliza="INDIVIDUAL",
            numero_documento=f"DOC{uuid4().hex[:6]}",
            tipo_documento="CC",
            nombres="María",
            apellidos="Test",
            fecha_inicio_poliza=date(2024, 1, 1),
            estado=EstadoAfiliado.ACTIVO,
        )
        db_session.add(afiliado)
        await db_session.flush()
        emp_id = None
        emp_empresa_id = None
        afiliado_id = afiliado.id

    inc = Incapacidad(
        numero=f"INC-TEST-{uuid4().hex[:8]}",
        tipo=tipo,
        estado=EstadoIncapacidad.EN_AUDITORIA,
        prioridad=Prioridad.NORMAL,
        fecha_inicio=date(2026, 1, 1),
        fecha_fin=date(2026, 1, 10),
        dias_totales=10,
        diagnostico_cie10="M545",
        descripcion_diagnostico="Lumbago no especificado",
        nombre_medico="Dr. García",
        registro_medico="RM12345",
        subtipo="ENFERMEDAD_LABORAL" if tipo == TipoIncapacidad.ARL else None,
        fecha_radicacion=datetime.utcnow(),
        empleado_id=emp_id,
        empresa_id=emp_empresa_id,
        afiliado_id=afiliado_id,
        siniestro_id=siniestro_id,
    )
    db_session.add(inc)
    await db_session.commit()
    await db_session.refresh(inc)
    return inc


async def _make_auditor(db_session):
    from app.models.usuario import Usuario
    from app.utils.enums import RolUsuario, EstadoUsuario
    from app.core.security import get_password_hash

    u = Usuario(
        username=f"aud_{uuid4().hex[:6]}",
        email=f"aud_{uuid4().hex[:6]}@test.com",
        password_hash=get_password_hash("Test123!"),
        nombre_completo="Auditor Test",
        rol=RolUsuario.AUDITOR,
        estado=EstadoUsuario.ACTIVO,
    )
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    return u


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_estado_invalido(db_session):
    """InvalidStateException when incapacidad is not EN_AUDITORIA."""
    from app.models.incapacidad import Incapacidad
    from app.models.afiliado import Afiliado
    from app.utils.enums import EstadoAfiliado

    afiliado = Afiliado(
        numero_poliza=f"POL-{uuid4().hex[:6]}",
        tipo_poliza="INDIVIDUAL",
        numero_documento=f"DOC{uuid4().hex[:6]}",
        tipo_documento="CC",
        nombres="Test",
        apellidos="Test",
        fecha_inicio_poliza=date(2024, 1, 1),
        estado=EstadoAfiliado.ACTIVO,
    )
    db_session.add(afiliado)
    await db_session.flush()

    inc = Incapacidad(
        numero=f"INC-TEST-{uuid4().hex[:8]}",
        tipo=TipoIncapacidad.SALUD,
        estado=EstadoIncapacidad.RADICADA,
        prioridad=Prioridad.NORMAL,
        fecha_inicio=date(2026, 1, 1),
        fecha_fin=date(2026, 1, 10),
        dias_totales=10,
        diagnostico_cie10="M545",
        fecha_radicacion=datetime.utcnow(),
        afiliado_id=afiliado.id,
    )
    db_session.add(inc)
    await db_session.commit()
    await db_session.refresh(inc)

    from app.services.incapacidad_service import incapacidad_service
    auditor = await _make_auditor(db_session)
    req = _make_request()

    with pytest.raises(InvalidStateException):
        await incapacidad_service.aprobar_en_auditoria(db_session, inc.id, req, auditor.id)


@pytest.mark.asyncio
async def test_observacion_corta():
    """Pydantic raises ValidationError for observacion shorter than 10 chars."""
    with pytest.raises(ValidationError):
        _make_request(observacion="corto")


@pytest.mark.asyncio
async def test_fechas_invertidas():
    """Pydantic raises ValidationError when fecha_fin < fecha_inicio."""
    with pytest.raises(ValidationError):
        _make_request(
            fecha_inicio_aprobada=date(2026, 1, 10),
            fecha_fin_aprobada=date(2026, 1, 1),
        )


@pytest.mark.asyncio
async def test_arl_sin_siniestro_error(db_session):
    """ARL without siniestro raises BadRequestException (SINIESTRO_REQUERIDO)."""
    inc = await _make_incapacidad_en_auditoria(db_session, tipo=TipoIncapacidad.ARL)
    auditor = await _make_auditor(db_session)
    req = _make_request()

    from app.services.incapacidad_service import incapacidad_service
    with pytest.raises(BadRequestException) as exc_info:
        await incapacidad_service.aprobar_en_auditoria(db_session, inc.id, req, auditor.id)

    assert exc_info.value.details is not None
    reglas = exc_info.value.details.get("reglas_fallidas", [])
    codigos = [r["codigo"] for r in reglas]
    assert "SINIESTRO_REQUERIDO" in codigos


@pytest.mark.asyncio
async def test_auditoria_resultado_persiste_en_error(db_session):
    """auditoria_resultado rows are written even when validation fails (always)."""
    from sqlalchemy import select as sa_select
    from app.models.auditoria_resultado import AuditoriaResultado

    inc = await _make_incapacidad_en_auditoria(db_session, tipo=TipoIncapacidad.ARL)
    auditor = await _make_auditor(db_session)
    req = _make_request()

    from app.services.incapacidad_service import incapacidad_service
    try:
        await incapacidad_service.aprobar_en_auditoria(db_session, inc.id, req, auditor.id)
    except BadRequestException:
        pass

    # Rows must exist in DB after the failed attempt
    rows = (await db_session.execute(
        sa_select(AuditoriaResultado).where(AuditoriaResultado.incapacidad_id == inc.id)
    )).scalars().all()
    assert len(rows) > 0, "auditoria_resultado rows must be persisted even on error"


@pytest.mark.asyncio
async def test_aprobacion_completa_mismo_periodo(db_session):
    """Same dates/days as original → estado LIQUIDACION."""
    inc = await _make_incapacidad_en_auditoria(db_session, tipo=TipoIncapacidad.SALUD)
    auditor = await _make_auditor(db_session)
    # Same dates as the incapacidad (2026-01-01 to 2026-01-10, 10 days)
    req = _make_request(
        fecha_inicio_aprobada=date(2026, 1, 1),
        fecha_fin_aprobada=date(2026, 1, 10),
    )

    from app.services.incapacidad_service import incapacidad_service
    result = await incapacidad_service.aprobar_en_auditoria(db_session, inc.id, req, auditor.id)

    assert result["estado"] == EstadoIncapacidad.LIQUIDACION.value


@pytest.mark.asyncio
async def test_aprobacion_parcial_fechas_distintas(db_session):
    """Different dates → estado LIQUIDACION_PARCIAL."""
    inc = await _make_incapacidad_en_auditoria(db_session, tipo=TipoIncapacidad.SALUD)
    auditor = await _make_auditor(db_session)
    # Shorter period: 2026-01-01 to 2026-01-05 (5 days, original is 10)
    req = _make_request(
        fecha_inicio_aprobada=date(2026, 1, 1),
        fecha_fin_aprobada=date(2026, 1, 5),
    )

    from app.services.incapacidad_service import incapacidad_service
    result = await incapacidad_service.aprobar_en_auditoria(db_session, inc.id, req, auditor.id)

    assert result["estado"] == EstadoIncapacidad.LIQUIDACION_PARCIAL.value


@pytest.mark.asyncio
async def test_texto_copiable_en_respuesta(db_session):
    """Response includes a non-empty texto_copiable string."""
    inc = await _make_incapacidad_en_auditoria(db_session, tipo=TipoIncapacidad.SALUD)
    auditor = await _make_auditor(db_session)
    req = _make_request()

    from app.services.incapacidad_service import incapacidad_service
    result = await incapacidad_service.aprobar_en_auditoria(db_session, inc.id, req, auditor.id)

    assert isinstance(result["texto_copiable"], str)
    assert len(result["texto_copiable"]) > 0


@pytest.mark.asyncio
async def test_plantilla_auditoria_creada(db_session):
    """PlantillaAuditoria row is created after successful approval."""
    from sqlalchemy import select as sa_select
    from app.models.plantilla_auditoria import PlantillaAuditoria

    inc = await _make_incapacidad_en_auditoria(db_session, tipo=TipoIncapacidad.SALUD)
    auditor = await _make_auditor(db_session)
    req = _make_request(canal_recepcion="Imaginex", nombre_ips="IPS Test")

    from app.services.incapacidad_service import incapacidad_service
    await incapacidad_service.aprobar_en_auditoria(db_session, inc.id, req, auditor.id)

    plantilla = (await db_session.execute(
        sa_select(PlantillaAuditoria).where(PlantillaAuditoria.incapacidad_id == inc.id)
    )).scalar_one_or_none()

    assert plantilla is not None
    assert plantilla.canal_recepcion == "Imaginex"
    assert plantilla.nombre_ips == "IPS Test"
    assert plantilla.dias_autorizados == 10
