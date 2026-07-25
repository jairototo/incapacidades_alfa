import pytest
from datetime import date, datetime
from app.models.incapacidad import Incapacidad
from app.models.siniestro import Siniestro
from app.models.usuario import Usuario
from app.utils.enums import (
    TipoIncapacidad,
    EstadoIncapacidad,
    RolUsuario,
    EstadoUsuario,
    TipoSiniestro,
    GravedadSiniestro,
    EstadoSiniestro,
    SyncSource,
)
from app.core.security import get_password_hash
from app.services.incapacidad_service import incapacidad_service


async def _make_siniestro(db_session, empleado_id, empresa_id, numero):
    # auditar_incapacidad's ARL "SINIESTRO_REQUERIDO" gate blocks RECHAZAR/APROBAR transitions
    # to a terminal estado unless the ARL incapacidad has a linked siniestro_id.
    s = Siniestro(
        numero_siniestro=numero,
        empleado_id=empleado_id,
        empresa_id=empresa_id,
        fecha_siniestro=date(2026, 6, 1),
        tipo_siniestro=TipoSiniestro.ACCIDENTE_TRABAJO,
        descripcion="Siniestro de prueba para carga de auditor",
        gravedad=GravedadSiniestro.LEVE,
        estado=EstadoSiniestro.REPORTADO,
        sync_source=SyncSource.MANUAL,
        fecha_reporte=datetime.utcnow(),
    )
    db_session.add(s)
    await db_session.commit()
    await db_session.refresh(s)
    return s


async def _make_auditor(db_session, carga):
    u = Usuario(
        username="test.carga.auditor", email="test.carga.auditor@segurosalfa-test.com.co",
        password_hash=get_password_hash("Test123!"), nombre_completo="Auditor Carga Test",
        rol=RolUsuario.AUDITOR, estado=EstadoUsuario.ACTIVO,
        incapacidades_asignadas_activas=carga,
    )
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    return u


@pytest.mark.asyncio
async def test_decrements_on_liquidacion(db_session, test_empleado, test_empresa):
    auditor = await _make_auditor(db_session, carga=3)
    siniestro = await _make_siniestro(
        db_session, test_empleado.id, test_empresa.id, "SIN-CARGA-001"
    )
    inc = Incapacidad(
        numero="ARL-CARGA-001", tipo=TipoIncapacidad.ARL, empleado_id=test_empleado.id,
        empresa_id=test_empresa.id, fecha_inicio=date(2026, 6, 1), fecha_fin=date(2026, 6, 5),
        dias_totales=5, estado=EstadoIncapacidad.EN_AUDITORIA, fecha_radicacion=datetime.utcnow(),
        auditor_asignado_id=auditor.id, siniestro_id=siniestro.id,
    )
    db_session.add(inc)
    await db_session.commit()

    await incapacidad_service.auditar_incapacidad(
        db=db_session, incapacidad_id=inc.id, accion="RECHAZAR", observaciones="Sin soporte médico",
    )

    await db_session.refresh(auditor)
    assert auditor.incapacidades_asignadas_activas == 2


@pytest.mark.asyncio
async def test_reincrements_on_devolution_to_en_auditoria(db_session, test_empleado, test_empresa):
    from app.services.liquidacion_service import liquidacion_service

    auditor = await _make_auditor(db_session, carga=2)
    inc = Incapacidad(
        numero="ARL-CARGA-002", tipo=TipoIncapacidad.ARL, empleado_id=test_empleado.id,
        empresa_id=test_empresa.id, fecha_inicio=date(2026, 6, 1), fecha_fin=date(2026, 6, 5),
        dias_totales=5, estado=EstadoIncapacidad.LIQUIDACION, fecha_radicacion=datetime.utcnow(),
        auditor_asignado_id=auditor.id,
    )
    db_session.add(inc)
    await db_session.commit()

    await liquidacion_service.devolver_a_auditoria(
        db=db_session, incapacidad_id=inc.id, observacion="Datos incompletos", liquidador_id=auditor.id,
    )

    await db_session.refresh(auditor)
    assert auditor.incapacidades_asignadas_activas == 3


@pytest.mark.asyncio
async def test_noop_when_no_auditor_assigned(db_session, test_empleado, test_empresa):
    siniestro = await _make_siniestro(
        db_session, test_empleado.id, test_empresa.id, "SIN-CARGA-003"
    )
    inc = Incapacidad(
        numero="ARL-CARGA-003", tipo=TipoIncapacidad.ARL, empleado_id=test_empleado.id,
        empresa_id=test_empresa.id, fecha_inicio=date(2026, 6, 1), fecha_fin=date(2026, 6, 5),
        dias_totales=5, estado=EstadoIncapacidad.EN_AUDITORIA, fecha_radicacion=datetime.utcnow(),
        siniestro_id=siniestro.id,
    )
    db_session.add(inc)
    await db_session.commit()

    # Should not raise even with no auditor_asignado_id
    await incapacidad_service.auditar_incapacidad(
        db=db_session, incapacidad_id=inc.id, accion="RECHAZAR", observaciones="Sin soporte médico",
    )
