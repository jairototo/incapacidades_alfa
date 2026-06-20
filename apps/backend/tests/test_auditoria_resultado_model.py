import pytest
from sqlalchemy import select
from app.models.auditoria_resultado import AuditoriaResultado


@pytest.mark.asyncio
async def test_can_persist_pass_and_fail(db_session, test_incapacidad):
    db_session.add_all([
        AuditoriaResultado(incapacidad_id=test_incapacidad.id, regla="R1", categoria="BUSINESS_RULE", aprobado=True, severidad="INFO"),
        AuditoriaResultado(incapacidad_id=test_incapacidad.id, regla="R2", categoria="FIELD_VALIDATION", aprobado=False, severidad="ERROR", detalle="x"),
    ])
    await db_session.flush()
    rows = (await db_session.execute(
        select(AuditoriaResultado).where(AuditoriaResultado.incapacidad_id == test_incapacidad.id)
    )).scalars().all()
    assert {r.aprobado for r in rows} == {True, False}
