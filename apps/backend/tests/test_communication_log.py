import pytest
from sqlalchemy import select
from app.models.communication_log import CommunicationLog


@pytest.mark.asyncio
async def test_communication_log_links_to_incapacidad(db_session, test_incapacidad):
    log = CommunicationLog(incapacidad_id=test_incapacidad.id, sistema="SERVIALFA", estado="PENDING",
                           payload_resumen={"numero": test_incapacidad.numero})
    db_session.add(log)
    await db_session.flush()
    found = (await db_session.execute(
        select(CommunicationLog).where(CommunicationLog.incapacidad_id == test_incapacidad.id)
    )).scalars().all()
    assert len(found) == 1 and found[0].sistema == "SERVIALFA"
    assert found[0].payload_resumen == {"numero": test_incapacidad.numero}
