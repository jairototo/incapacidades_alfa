import pytest
from app.services.solicitante_resolver import resolve_solicitante_for_empresa
from app.models.empresa import Empresa


@pytest.mark.asyncio
async def test_creates_solicitante_when_absent(db_session):
    empresa = Empresa(nit="900111", razon_social="ACME SA", email_contacto="rrhh@acme.com", estado="ACTIVA")
    db_session.add(empresa); await db_session.flush()
    s = await resolve_solicitante_for_empresa(db_session, empresa)
    assert s.correo == "rrhh@acme.com"
    assert s.nombres  # derived from razon_social

@pytest.mark.asyncio
async def test_reuses_existing_solicitante(db_session):
    empresa = Empresa(nit="900222", razon_social="BETA SA", email_contacto="info@beta.com", estado="ACTIVA")
    db_session.add(empresa); await db_session.flush()
    first = await resolve_solicitante_for_empresa(db_session, empresa)
    await db_session.flush()
    second = await resolve_solicitante_for_empresa(db_session, empresa)
    assert first.id == second.id
