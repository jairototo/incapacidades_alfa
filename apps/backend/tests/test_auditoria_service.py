import datetime as dt
import pytest
from sqlalchemy import select
from app.services.auditoria_service import auditar_incapacidad, _incapacidad_to_row
from app.models.auditoria_resultado import AuditoriaResultado
from app.models.incapacidad import Incapacidad
from app.models.siniestro import Siniestro
from app.utils.enums import TipoIncapacidad, EstadoIncapacidad, TipoSiniestro, GravedadSiniestro, EstadoSiniestro
from app.services.incapacidad_service import ALLOWED_TRANSITIONS, incapacidad_service


@pytest.mark.asyncio
async def test_audit_persists_results_and_transitions(db_session, test_empleado, test_empresa):
    from app.models.usuario import Usuario
    from app.utils.enums import RolUsuario, EstadoUsuario
    from app.core.security import get_password_hash

    default_auditor = Usuario(
        username="auditor_default", email="auditor.default@segurosalfa-test.com.co",
        password_hash=get_password_hash("Test123!"), nombre_completo="Auditor por Defecto",
        rol=RolUsuario.AUDITOR, estado=EstadoUsuario.ACTIVO,
    )
    db_session.add(default_auditor)
    await db_session.commit()

    inc = Incapacidad(
        numero="ARL-AUDIT-0001", tipo=TipoIncapacidad.ARL,
        empleado_id=test_empleado.id, empresa_id=test_empresa.id,
        fecha_inicio=dt.date(2026, 6, 1), fecha_fin=dt.date(2026, 6, 5), dias_totales=999,  # deliberate mismatch
        diagnostico_cie10="S00.0", nombre_medico="Dr X", registro_medico="RM-1",
        estado=EstadoIncapacidad.RADICADA, fecha_radicacion=dt.datetime.utcnow(),
    )
    db_session.add(inc); await db_session.flush()

    await auditar_incapacidad(db_session, inc.id)

    resultados = (await db_session.execute(
        select(AuditoriaResultado).where(AuditoriaResultado.incapacidad_id == inc.id)
    )).scalars().all()
    assert len(resultados) >= 1
    assert any(r.aprobado is False and r.regla == "DIAS_TOTALES_MISMATCH" for r in resultados)  # mismatch fails
    assert any(r.aprobado is True for r in resultados)  # other rules pass

    refreshed = (await db_session.execute(select(Incapacidad).where(Incapacidad.id == inc.id))).scalar_one()
    assert refreshed.estado == EstadoIncapacidad.EN_AUDITORIA


@pytest.mark.asyncio
async def test_audit_assigns_default_auditor_when_no_siniestro(db_session, test_empleado, test_empresa):
    from app.models.usuario import Usuario
    from app.utils.enums import RolUsuario, EstadoUsuario
    from app.core.security import get_password_hash

    default_auditor = Usuario(
        username="auditor_default", email="auditor.default@segurosalfa-test.com.co",
        password_hash=get_password_hash("Test123!"), nombre_completo="Auditor por Defecto",
        rol=RolUsuario.AUDITOR, estado=EstadoUsuario.ACTIVO,
    )
    db_session.add(default_auditor)
    await db_session.commit()

    inc = Incapacidad(
        numero="ARL-AUDIT-ASIG01", tipo=TipoIncapacidad.ARL,
        empleado_id=test_empleado.id, empresa_id=test_empresa.id,
        fecha_inicio=dt.date(2026, 6, 1), fecha_fin=dt.date(2026, 6, 5), dias_totales=5,
        diagnostico_cie10="S00.0", nombre_medico="Dr X", registro_medico="RM-ASIG1",
        estado=EstadoIncapacidad.RADICADA, fecha_radicacion=dt.datetime.utcnow(),
    )
    db_session.add(inc)
    await db_session.flush()

    await auditar_incapacidad(db_session, inc.id)

    refreshed = (await db_session.execute(select(Incapacidad).where(Incapacidad.id == inc.id))).scalar_one()
    assert refreshed.auditor_asignado_id == default_auditor.id


# --- Unit tests: ALLOWED_TRANSITIONS for CREACION_SINIESTRO ---

def test_creacion_siniestro_allowed_transitions():
    """CREACION_SINIESTRO must transition only back to EN_AUDITORIA (Celery task routes it)."""
    allowed = ALLOWED_TRANSITIONS[EstadoIncapacidad.CREACION_SINIESTRO]
    assert allowed == [EstadoIncapacidad.EN_AUDITORIA]
    assert EstadoIncapacidad.LIQUIDACION not in allowed
    assert EstadoIncapacidad.GLOSADA not in allowed


def test_en_auditoria_allows_creacion_siniestro():
    """EN_AUDITORIA must allow transition to CREACION_SINIESTRO."""
    allowed = ALLOWED_TRANSITIONS[EstadoIncapacidad.EN_AUDITORIA]
    assert EstadoIncapacidad.CREACION_SINIESTRO in allowed


# --- Integration test: auditar_incapacidad with CREACION_SINIESTRO action ---

@pytest.mark.asyncio
async def test_auditar_accion_creacion_siniestro(db_session, test_empleado, test_empresa):
    """auditar_incapacidad with accion=CREACION_SINIESTRO transitions EN_AUDITORIA → CREACION_SINIESTRO."""
    inc = Incapacidad(
        numero="ARL-AUDIT-CS01", tipo=TipoIncapacidad.ARL,
        empleado_id=test_empleado.id, empresa_id=test_empresa.id,
        fecha_inicio=dt.date(2026, 6, 1), fecha_fin=dt.date(2026, 6, 5), dias_totales=4,
        diagnostico_cie10="S00.0", nombre_medico="Dr X", registro_medico="RM-CS1",
        estado=EstadoIncapacidad.EN_AUDITORIA, fecha_radicacion=dt.datetime.utcnow(),
    )
    db_session.add(inc)
    await db_session.flush()

    result = await incapacidad_service.auditar_incapacidad(
        db=db_session,
        incapacidad_id=inc.id,
        accion="CREACION_SINIESTRO",
        observaciones="Requiere creación de siniestro en sistema ARL",
    )

    assert result.estado == EstadoIncapacidad.CREACION_SINIESTRO


# --- Unit test: _incapacidad_to_row with a linked Siniestro (Fix 1 regression) ---

def test_incapacidad_to_row_with_siniestro():
    """_incapacidad_to_row must read fecha_siniestro (not fecha_accidente) without AttributeError."""

    class FakeSiniestro:
        fecha_siniestro = dt.date(2026, 3, 15)

    class FakeEmpleado:
        numero_documento = "12345678"

    class FakeInc:
        tipo = TipoIncapacidad.ARL
        empleado = FakeEmpleado()
        subtipo = "ACCIDENTE"
        fecha_inicio = dt.date(2026, 3, 15)
        fecha_fin = dt.date(2026, 3, 20)
        dias_totales = 5
        diagnostico_cie10 = "S00.0"
        nombre_medico = "Dr Test"
        registro_medico = "RM-001"
        siniestro_id = None
        siniestro = FakeSiniestro()

    row = _incapacidad_to_row(FakeInc())

    assert row["fecha_siniestro"] == dt.date(2026, 3, 15), (
        "fecha_siniestro debe leerse del modelo Siniestro.fecha_siniestro, no fecha_accidente"
    )


def test_incapacidad_to_row_without_siniestro():
    """_incapacidad_to_row returns None for fecha_siniestro when inc.siniestro is None."""

    class FakeEmpleado:
        numero_documento = "87654321"

    class FakeInc:
        tipo = TipoIncapacidad.ARL
        empleado = FakeEmpleado()
        subtipo = None
        fecha_inicio = dt.date(2026, 1, 1)
        fecha_fin = dt.date(2026, 1, 5)
        dias_totales = 4
        diagnostico_cie10 = "A00.0"
        nombre_medico = "Dr Otro"
        registro_medico = "RM-002"
        siniestro_id = None
        siniestro = None

    row = _incapacidad_to_row(FakeInc())

    assert row["fecha_siniestro"] is None
