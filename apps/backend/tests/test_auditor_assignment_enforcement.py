"""
Enforcement: un usuario con rol AUDITOR solo puede gestionar (auditar / aprobar-en-auditoria)
incapacidades cuyo auditor_asignado_id coincide con su propio id. ADMIN no tiene esta
restricción (bypass total). Este es el bloqueo de backend que respalda el filtro de la
bandeja de pendientes — un auditor no debe poder gestionar por API directa una incapacidad
que la bandeja ya le oculta.
"""
import pytest
from datetime import date, datetime

from app.core.exceptions import ForbiddenException
from app.models.incapacidad import Incapacidad
from app.models.siniestro import Siniestro
from app.models.usuario import Usuario
from app.utils.enums import (
    TipoIncapacidad, EstadoIncapacidad, RolUsuario, EstadoUsuario,
    TipoSiniestro, GravedadSiniestro, EstadoSiniestro, SyncSource,
)
from app.core.security import get_password_hash
from app.services.incapacidad_service import incapacidad_service


async def _make_auditor(db_session, username):
    u = Usuario(
        username=username, email=f"{username}@segurosalfa-test.com.co",
        password_hash=get_password_hash("Test123!"), nombre_completo=username,
        rol=RolUsuario.AUDITOR, estado=EstadoUsuario.ACTIVO,
    )
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    return u


async def _make_siniestro(db_session, empleado_id, empresa_id, numero):
    # auditar_incapacidad's ARL "SINIESTRO_REQUERIDO" gate blocks RECHAZAR/APROBAR
    # transitions to a terminal estado unless the ARL incapacidad has a linked siniestro_id.
    s = Siniestro(
        numero_siniestro=numero, empleado_id=empleado_id, empresa_id=empresa_id,
        fecha_siniestro=date(2026, 6, 1), tipo_siniestro=TipoSiniestro.ACCIDENTE_TRABAJO,
        descripcion="Siniestro de prueba para enforcement de asignación",
        gravedad=GravedadSiniestro.LEVE, estado=EstadoSiniestro.REPORTADO,
        sync_source=SyncSource.MANUAL, fecha_reporte=datetime.utcnow(),
    )
    db_session.add(s)
    await db_session.commit()
    await db_session.refresh(s)
    return s


async def _make_incapacidad_en_auditoria(db_session, test_empleado, test_empresa, auditor_asignado_id, numero):
    siniestro = await _make_siniestro(db_session, test_empleado.id, test_empresa.id, f"SIN-{numero}")
    inc = Incapacidad(
        numero=numero, tipo=TipoIncapacidad.ARL, empleado_id=test_empleado.id,
        empresa_id=test_empresa.id, fecha_inicio=date(2026, 6, 1), fecha_fin=date(2026, 6, 5),
        dias_totales=5, diagnostico_cie10="S00.0", nombre_medico="Dr X", registro_medico="RM-1",
        estado=EstadoIncapacidad.EN_AUDITORIA, fecha_radicacion=datetime.utcnow(),
        auditor_asignado_id=auditor_asignado_id, siniestro_id=siniestro.id,
    )
    db_session.add(inc)
    await db_session.commit()
    await db_session.refresh(inc)
    return inc


@pytest.mark.asyncio
async def test_auditar_incapacidad_forbidden_for_unassigned_auditor(db_session, test_empleado, test_empresa):
    auditor_asignado = await _make_auditor(db_session, "test.enforce.owner")
    otro_auditor = await _make_auditor(db_session, "test.enforce.other")
    inc = await _make_incapacidad_en_auditoria(
        db_session, test_empleado, test_empresa, auditor_asignado.id, "ARL-ENFORCE-001"
    )

    with pytest.raises(ForbiddenException):
        await incapacidad_service.auditar_incapacidad(
            db=db_session, incapacidad_id=inc.id, accion="RECHAZAR",
            observaciones="Sin soporte médico", usuario_id=otro_auditor.id,
            usuario_rol=RolUsuario.AUDITOR,
        )


@pytest.mark.asyncio
async def test_auditar_incapacidad_allowed_for_assigned_auditor(db_session, test_empleado, test_empresa):
    auditor_asignado = await _make_auditor(db_session, "test.enforce.owner2")
    inc = await _make_incapacidad_en_auditoria(
        db_session, test_empleado, test_empresa, auditor_asignado.id, "ARL-ENFORCE-002"
    )

    result = await incapacidad_service.auditar_incapacidad(
        db=db_session, incapacidad_id=inc.id, accion="RECHAZAR",
        observaciones="Sin soporte médico", usuario_id=auditor_asignado.id,
        usuario_rol=RolUsuario.AUDITOR,
    )

    assert result.estado == EstadoIncapacidad.GLOSADA


@pytest.mark.asyncio
async def test_auditar_incapacidad_allowed_for_admin_regardless_of_assignment(db_session, test_empleado, test_empresa):
    auditor_asignado = await _make_auditor(db_session, "test.enforce.owner3")
    admin = Usuario(
        username="test.enforce.admin", email="test.enforce.admin@segurosalfa-test.com.co",
        password_hash=get_password_hash("Test123!"), nombre_completo="Admin Enforcement Test",
        rol=RolUsuario.ADMIN, estado=EstadoUsuario.ACTIVO,
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)

    inc = await _make_incapacidad_en_auditoria(
        db_session, test_empleado, test_empresa, auditor_asignado.id, "ARL-ENFORCE-003"
    )

    result = await incapacidad_service.auditar_incapacidad(
        db=db_session, incapacidad_id=inc.id, accion="RECHAZAR",
        observaciones="Sin soporte médico", usuario_id=admin.id,
        usuario_rol=RolUsuario.ADMIN,
    )

    assert result.estado == EstadoIncapacidad.GLOSADA


@pytest.mark.asyncio
async def test_auditar_incapacidad_allowed_when_usuario_rol_not_provided(db_session, test_empleado, test_empresa):
    """Llamadas internas/tests que no pasan usuario_rol no deben quedar bloqueadas (compatibilidad)."""
    auditor_asignado = await _make_auditor(db_session, "test.enforce.owner4")
    inc = await _make_incapacidad_en_auditoria(
        db_session, test_empleado, test_empresa, auditor_asignado.id, "ARL-ENFORCE-004"
    )

    result = await incapacidad_service.auditar_incapacidad(
        db=db_session, incapacidad_id=inc.id, accion="RECHAZAR",
        observaciones="Sin soporte médico",
    )

    assert result.estado == EstadoIncapacidad.GLOSADA


@pytest.mark.asyncio
async def test_aprobar_en_auditoria_forbidden_for_unassigned_auditor(db_session, test_empleado, test_empresa):
    from app.schemas.incapacidad import AprobarAuditoriaRequest

    auditor_asignado = await _make_auditor(db_session, "test.enforce.owner5")
    otro_auditor = await _make_auditor(db_session, "test.enforce.other2")
    inc = await _make_incapacidad_en_auditoria(
        db_session, test_empleado, test_empresa, auditor_asignado.id, "ARL-ENFORCE-005"
    )

    body = AprobarAuditoriaRequest(
        fecha_inicio_aprobada=date(2026, 6, 1),
        fecha_fin_aprobada=date(2026, 6, 5),
        canal_recepcion="EMAIL",
        observacion="Aprobado con todos los soportes",
    )

    with pytest.raises(ForbiddenException):
        await incapacidad_service.aprobar_en_auditoria(
            db=db_session, incapacidad_id=inc.id, data=body,
            usuario_id=otro_auditor.id, usuario_rol=RolUsuario.AUDITOR,
        )
