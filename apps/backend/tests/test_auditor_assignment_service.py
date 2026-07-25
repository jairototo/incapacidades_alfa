import pytest
from datetime import date, datetime
from app.services.auditor_assignment_service import asignar_auditor
from app.models.incapacidad import Incapacidad
from app.models.siniestro import Siniestro
from app.models.usuario import Usuario
from app.utils.enums import (
    TipoIncapacidad, EstadoIncapacidad, TipoSiniestro, GravedadSiniestro,
    EstadoSiniestro, RolUsuario, EstadoUsuario, SucursalSiniestro,
)
from app.core.security import get_password_hash


async def _make_auditor(db_session, username, sucursal, carga=0):
    u = Usuario(
        username=username, email=f"{username}@segurosalfa-test.com.co",
        password_hash=get_password_hash("Test123!"), nombre_completo=username,
        rol=RolUsuario.AUDITOR, estado=EstadoUsuario.ACTIVO,
        sucursal=sucursal, incapacidades_asignadas_activas=carga,
    )
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    return u


async def _make_default_auditor(db_session):
    u = Usuario(
        username="auditor_default", email="auditor.default@segurosalfa-test.com.co",
        password_hash=get_password_hash("Test123!"), nombre_completo="Auditor por Defecto",
        rol=RolUsuario.AUDITOR, estado=EstadoUsuario.ACTIVO,
    )
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    return u


@pytest.mark.asyncio
async def test_assigns_by_sucursal_of_active_siniestro(db_session, test_empleado, test_empresa):
    auditor_cali = await _make_auditor(db_session, "test.cali", SucursalSiniestro.CALI)
    sin = Siniestro(
        numero_siniestro="SIN-CALI-001", empleado_id=test_empleado.id, empresa_id=test_empresa.id,
        fecha_siniestro=date(2026, 5, 1), tipo_siniestro=TipoSiniestro.ACCIDENTE_TRABAJO,
        descripcion="x", gravedad=GravedadSiniestro.LEVE, estado=EstadoSiniestro.REPORTADO,
        sucursal=SucursalSiniestro.CALI,
    )
    db_session.add(sin)
    await db_session.commit()

    inc = Incapacidad(
        numero="ARL-ASIG-001", tipo=TipoIncapacidad.ARL, empleado_id=test_empleado.id,
        empresa_id=test_empresa.id, fecha_inicio=date(2026, 5, 2), fecha_fin=date(2026, 5, 10),
        dias_totales=8, estado=EstadoIncapacidad.EN_AUDITORIA, fecha_radicacion=datetime.utcnow(),
    )
    db_session.add(inc)
    await db_session.commit()

    auditor = await asignar_auditor(db_session, inc)

    assert auditor.id == auditor_cali.id
    assert inc.auditor_asignado_id == auditor_cali.id
    await db_session.refresh(auditor_cali)
    assert auditor_cali.incapacidades_asignadas_activas == 1


@pytest.mark.asyncio
async def test_load_balances_between_auditors_same_sucursal(db_session, test_empleado, test_empresa):
    busy = await _make_auditor(db_session, "test.bta.busy", SucursalSiniestro.BOGOTA, carga=5)
    idle = await _make_auditor(db_session, "test.bta.idle", SucursalSiniestro.BOGOTA, carga=1)
    sin = Siniestro(
        numero_siniestro="SIN-BTA-001", empleado_id=test_empleado.id, empresa_id=test_empresa.id,
        fecha_siniestro=date(2026, 5, 1), tipo_siniestro=TipoSiniestro.ACCIDENTE_TRABAJO,
        descripcion="x", gravedad=GravedadSiniestro.LEVE, estado=EstadoSiniestro.EN_INVESTIGACION,
        sucursal=SucursalSiniestro.BOGOTA,
    )
    db_session.add(sin)
    await db_session.commit()

    inc = Incapacidad(
        numero="ARL-ASIG-002", tipo=TipoIncapacidad.ARL, empleado_id=test_empleado.id,
        empresa_id=test_empresa.id, fecha_inicio=date(2026, 5, 3), fecha_fin=date(2026, 5, 10),
        dias_totales=7, estado=EstadoIncapacidad.EN_AUDITORIA, fecha_radicacion=datetime.utcnow(),
    )
    db_session.add(inc)
    await db_session.commit()

    auditor = await asignar_auditor(db_session, inc)

    assert auditor.id == idle.id
    assert busy.incapacidades_asignadas_activas == 5  # unchanged


@pytest.mark.asyncio
async def test_falls_back_to_default_when_no_siniestro(db_session, test_afiliado):
    default_auditor = await _make_default_auditor(db_session)

    inc = Incapacidad(
        numero="SALUD-ASIG-001", tipo=TipoIncapacidad.SALUD, afiliado_id=test_afiliado.id,
        fecha_inicio=date(2026, 5, 3), fecha_fin=date(2026, 5, 10), dias_totales=7,
        estado=EstadoIncapacidad.EN_AUDITORIA, fecha_radicacion=datetime.utcnow(),
    )
    db_session.add(inc)
    await db_session.commit()

    auditor = await asignar_auditor(db_session, inc)

    assert auditor.id == default_auditor.id
    assert inc.auditor_asignado_id == default_auditor.id


@pytest.mark.asyncio
async def test_falls_back_to_default_when_no_auditor_configured_for_sucursal(db_session, test_empleado, test_empresa):
    default_auditor = await _make_default_auditor(db_session)
    # No AUDITOR configured for CARTAGENA
    sin = Siniestro(
        numero_siniestro="SIN-CTG-001", empleado_id=test_empleado.id, empresa_id=test_empresa.id,
        fecha_siniestro=date(2026, 5, 1), tipo_siniestro=TipoSiniestro.ACCIDENTE_TRABAJO,
        descripcion="x", gravedad=GravedadSiniestro.LEVE, estado=EstadoSiniestro.REPORTADO,
        sucursal=SucursalSiniestro.CARTAGENA,
    )
    db_session.add(sin)
    await db_session.commit()

    inc = Incapacidad(
        numero="ARL-ASIG-003", tipo=TipoIncapacidad.ARL, empleado_id=test_empleado.id,
        empresa_id=test_empresa.id, fecha_inicio=date(2026, 5, 2), fecha_fin=date(2026, 5, 10),
        dias_totales=8, estado=EstadoIncapacidad.EN_AUDITORIA, fecha_radicacion=datetime.utcnow(),
    )
    db_session.add(inc)
    await db_session.commit()

    auditor = await asignar_auditor(db_session, inc)

    assert auditor.id == default_auditor.id


@pytest.mark.asyncio
async def test_raises_when_default_auditor_missing(db_session, test_afiliado):
    inc = Incapacidad(
        numero="SALUD-ASIG-002", tipo=TipoIncapacidad.SALUD, afiliado_id=test_afiliado.id,
        fecha_inicio=date(2026, 5, 3), fecha_fin=date(2026, 5, 10), dias_totales=7,
        estado=EstadoIncapacidad.EN_AUDITORIA, fecha_radicacion=datetime.utcnow(),
    )
    db_session.add(inc)
    await db_session.commit()

    with pytest.raises(RuntimeError, match="auditor_default"):
        await asignar_auditor(db_session, inc)


@pytest.mark.asyncio
async def test_raises_when_default_auditor_deactivated(db_session, test_afiliado):
    """
    Finding 4 (final review): un auditor_default INACTIVO (p. ej. desactivado
    por error desde AuditoresPage) debe fallar ruidosamente con RuntimeError,
    no asignarse silenciosamente a una cuenta deshabilitada.
    """
    u = Usuario(
        username="auditor_default", email="auditor.default.inactivo@segurosalfa-test.com.co",
        password_hash=get_password_hash("Test123!"), nombre_completo="Auditor por Defecto",
        rol=RolUsuario.AUDITOR, estado=EstadoUsuario.INACTIVO,
    )
    db_session.add(u)
    await db_session.commit()

    inc = Incapacidad(
        numero="SALUD-ASIG-003", tipo=TipoIncapacidad.SALUD, afiliado_id=test_afiliado.id,
        fecha_inicio=date(2026, 5, 3), fecha_fin=date(2026, 5, 10), dias_totales=7,
        estado=EstadoIncapacidad.EN_AUDITORIA, fecha_radicacion=datetime.utcnow(),
    )
    db_session.add(inc)
    await db_session.commit()

    with pytest.raises(RuntimeError, match="auditor_default"):
        await asignar_auditor(db_session, inc)


@pytest.mark.asyncio
async def test_asignar_auditor_is_idempotent_when_already_assigned(db_session, test_empleado, test_empresa):
    """
    Finding 2 (final review): si `incapacidad.auditor_asignado_id` ya está
    fijado (p. ej. redelivery de Celery), asignar_auditor debe retornar ese
    mismo auditor sin re-incrementar su carga ni reasignar a otro auditor
    distinto (incluso si ahora hay un auditor con menor carga disponible).
    """
    auditor_original = await _make_auditor(db_session, "test.cali.original", SucursalSiniestro.CALI, carga=2)
    auditor_libre = await _make_auditor(db_session, "test.cali.libre", SucursalSiniestro.CALI, carga=0)

    inc = Incapacidad(
        numero="ARL-ASIG-IDEMP01", tipo=TipoIncapacidad.ARL, empleado_id=test_empleado.id,
        empresa_id=test_empresa.id, fecha_inicio=date(2026, 5, 2), fecha_fin=date(2026, 5, 10),
        dias_totales=8, estado=EstadoIncapacidad.EN_AUDITORIA, fecha_radicacion=datetime.utcnow(),
        auditor_asignado_id=auditor_original.id,
    )
    db_session.add(inc)
    await db_session.commit()

    auditor = await asignar_auditor(db_session, inc)

    assert auditor.id == auditor_original.id
    await db_session.refresh(auditor_original)
    await db_session.refresh(auditor_libre)
    assert auditor_original.incapacidades_asignadas_activas == 2  # unchanged
    assert auditor_libre.incapacidades_asignadas_activas == 0  # never touched
