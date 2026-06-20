"""TDD test — ServiAlfa/Sicat stubs + IntegracionService.

Phase 3, Task 2: verifies that procesar() logs both SERVIALFA and SICAT attempts
to communication_log and stores the ServiAlfa number on the Incapacidad.
"""
import pytest
from sqlalchemy import select
from app.services.integracion.integracion_service import IntegracionService
from app.models.communication_log import CommunicationLog


@pytest.mark.asyncio
async def test_integracion_logs_servialfa_and_sicat(db_session, test_incapacidad):
    svc = IntegracionService(db_session)
    await svc.procesar(db_session, test_incapacidad)
    logs = (await db_session.execute(
        select(CommunicationLog).where(CommunicationLog.incapacidad_id == test_incapacidad.id)
    )).scalars().all()
    sistemas = {l.sistema for l in logs}
    assert {"SERVIALFA", "SICAT"} <= sistemas
    # ServiAlfa number stored on the incapacidad
    assert test_incapacidad.numero_radicacion_servialfa is not None
    # Sicat log references the servialfa number
    sicat = next(l for l in logs if l.sistema == "SICAT")
    assert sicat.payload_resumen.get("numero_radicacion_servialfa") == test_incapacidad.numero_radicacion_servialfa
