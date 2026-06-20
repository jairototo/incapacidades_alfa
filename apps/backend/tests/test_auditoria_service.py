import datetime as dt
import pytest
from sqlalchemy import select
from app.services.auditoria_service import auditar_incapacidad
from app.models.auditoria_resultado import AuditoriaResultado
from app.models.incapacidad import Incapacidad
from app.utils.enums import TipoIncapacidad, EstadoIncapacidad


@pytest.mark.asyncio
async def test_audit_persists_results_and_transitions(db_session, test_empleado, test_empresa):
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
